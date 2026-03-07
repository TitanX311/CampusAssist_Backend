"""
/api/users — user profile and stats endpoints.

Design
------
* ``GET /api/users/me``       — current user's full profile + stats (auth required)
* ``GET /api/users/{user_id}``— any user's public profile + stats (auth required)

Cache refresh
-------------
On every request we check whether the cached profile is stale (> STATS_CACHE_TTL_SECONDS
old).  If it is, we re-fetch from auth_service (gRPC) and the three downstream
services (HTTP) under a SELECT … FOR UPDATE lock, then upsert the result.

ACID guarantees
---------------
* The SELECT … FOR UPDATE in ``_get_or_refresh`` serialises concurrent refreshes
  for the same user — only one writer proceeds, the second will see the freshly
  written row after the first transaction commits.
* The ``get_db`` dependency commits on success and rolls back on exception, so
  the profile table is always left in a consistent state.
* ``statement_cache_size=0`` in the engine prevents asyncpg's prepared-statement
  cache from stripping the row lock from FOR UPDATE queries.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from user.config.database import get_db
from user.config.settings import get_settings
from user.dependencies.auth import TokenPayload, get_current_user
from user.grpc import auth_client
from user.grpc.stats_client import fetch_user_stats
from user.repositories.user_profile_repository import UserProfileRepository
from user.schemas.user import UserProfileResponse, UserStatsResponse

router = APIRouter(prefix="/api/users", tags=["Users"])
_bearer = HTTPBearer(auto_error=True)

_ERROR_401 = {"description": "Missing or invalid Bearer token."}
_ERROR_403 = {"description": "Insufficient permissions."}
_ERROR_404 = {"description": "User not found."}


class UpdateProfileRequest(BaseModel):
    """Fields a user may update on their own profile."""

    name: str | None = None
    picture: str | None = None


async def _get_or_refresh(
    user_id: str,
    db: AsyncSession,
    settings,
) -> UserProfileResponse:
    """
    Return a fresh UserProfileResponse for *user_id*.

    If the cached profile exists and is still within TTL, it is returned
    directly.  Otherwise we refresh from auth_service + downstream stats under
    a SELECT … FOR UPDATE lock to prevent lost updates.
    """
    repo = UserProfileRepository(db)
    now = datetime.now(timezone.utc)

    # Non-locking fast path — check if we have a valid cached entry.
    profile = await repo.get_by_id(user_id)

    ttl = settings.STATS_CACHE_TTL_SECONDS
    needs_refresh = (
        profile is None
        or profile.last_synced_at is None
        or (now - profile.last_synced_at).total_seconds() > ttl
    )

    if needs_refresh:
        # Acquire a row-level lock before refreshing to serialise concurrent
        # requests for the same user.
        locked = await repo.get_by_id_for_update(user_id)  # noqa: F841  (lock held until commit)

        # Re-read inside the lock — another concurrent request may have already
        # refreshed the row while we were waiting.
        profile = await repo.get_by_id(user_id)
        needs_refresh = (
            profile is None
            or profile.last_synced_at is None
            or (now - profile.last_synced_at).total_seconds() > ttl
        )

        if needs_refresh:
            # Fetch from auth_service and the three stats services in parallel.
            auth_data, stats = await asyncio.gather(
                auth_client.get_user(settings.AUTH_GRPC_TARGET, user_id),
                fetch_user_stats(
                    settings.POST_SERVICE_URL,
                    settings.COMMENT_SERVICE_URL,
                    settings.COMMUNITY_SERVICE_URL,
                    user_id,
                ),
            )

            if not auth_data.get("found"):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found.",
                )

            # Persist the refreshed data (under the lock).
            profile = await repo.upsert(
                user_id=user_id,
                email=auth_data.get("email"),
                name=auth_data.get("name"),
                picture=auth_data.get("picture"),
                user_type=auth_data.get("type", "USER"),
                is_active=bool(auth_data.get("is_active", True)),
                joined_at=None,  # auth_service proto doesn't expose created_at
                post_count=stats["post_count"],
                comment_count=stats["comment_count"],
                community_count=stats["community_count"],
            )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return UserProfileResponse(
        user_id=profile.user_id,
        email=profile.email,
        name=profile.name,
        picture=profile.picture,
        user_type=profile.user_type,
        is_active=profile.is_active,
        joined_at=profile.joined_at,
        stats=UserStatsResponse(
            post_count=profile.post_count,
            comment_count=profile.comment_count,
            community_count=profile.community_count,
        ),
    )


# ---------------------------------------------------------------------------
# GET /api/users/me
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user profile",
    description=(
        "Return the full profile and activity stats for the authenticated user.\n\n"
        "Stats are cached and refreshed when stale (default TTL: 5 minutes).\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {"description": "Current user profile with stats"},
        401: _ERROR_401,
    },
)
async def get_me(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    settings = get_settings()
    return await _get_or_refresh(current_user.user_id, db, settings)


@router.patch(
    "/me",
    response_model=UserProfileResponse,
    summary="Update current user profile",
    description=(
        "Update the authenticated user's display name and/or profile picture.\n\n"
        "The change is forwarded to auth_service (source of truth) and the local "
        "stats cache is immediately invalidated so the next read returns fresh data.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {"description": "Updated profile with stats"},
        401: _ERROR_401,
        404: _ERROR_404,
    },
)
async def update_me(
    body: UpdateProfileRequest,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    settings = get_settings()

    # Forward to auth_service — that is the source of truth for name/picture.
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.patch(
            f"{settings.AUTH_SERVICE_URL}/api/auth/me",
            json=body.model_dump(exclude_none=True),
            headers={"Authorization": f"Bearer {credentials.credentials}"},
        )
    if resp.status_code == 404:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.json().get("detail", resp.text))

    # Invalidate local cache so the next read re-fetches from auth_service.
    repo = UserProfileRepository(db)
    profile = await repo.get_by_id_for_update(current_user.user_id)
    if profile is not None:
        profile.last_synced_at = None  # force refresh on next GET
        await db.flush()

    return await _get_or_refresh(current_user.user_id, db, settings)


# ---------------------------------------------------------------------------
# GET /api/users/{user_id}
# ---------------------------------------------------------------------------


@router.get(
    "/{user_id}",
    response_model=UserProfileResponse,
    summary="Get user profile by ID",
    description=(
        "Return the public profile and activity stats for any user by their UUID.\n\n"
        "Stats are cached and refreshed when stale (default TTL: 5 minutes).\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {"description": "User profile with stats"},
        401: _ERROR_401,
        404: _ERROR_404,
    },
)
async def get_user_profile(
    user_id: str,
    _: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    settings = get_settings()
    return await _get_or_refresh(user_id, db, settings)
