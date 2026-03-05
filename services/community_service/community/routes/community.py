import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from community.config.database import get_db
from community.dependencies.auth import TokenPayload, get_current_user
from community.models.community import CommunityType
from community.repositories.community_repository import CommunityRepository
from community.schemas.community import (
    CommunityListResponse,
    CommunityResponse,
    JoinCommunityResponse,
    LeaveCommunityResponse,
)

router = APIRouter(prefix="/community", tags=["Community"])

_COMMUNITY_EXAMPLE = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "CS Department",
    "type": "PUBLIC",
    "member_users": ["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    "requested_users": [],
    "parent_colleges": ["f47ac10b-58cc-4372-a567-0e02b2c3d479"],
    "posts": [],
    "created_at": "2026-03-01T10:00:00+00:00",
    "updated_at": "2026-03-01T10:00:00+00:00",
}

_ERROR_401 = {
    "description": "Unauthorized — missing, expired, or invalid Bearer access token",
    "content": {"application/json": {"example": {"detail": "Not authenticated."}}},
}
_ERROR_404 = {
    "description": "Not Found — community with the given ID does not exist",
    "content": {"application/json": {"example": {"detail": "Community not found."}}},
}
_ERROR_409_MEMBER = {
    "description": "Conflict — user is already a member",
    "content": {"application/json": {"example": {"detail": "You are already a member of this community."}}},
}
_ERROR_409_REQUESTED = {
    "description": "Conflict — join request already pending",
    "content": {"application/json": {"example": {"detail": "You already have a pending join request for this community."}}},
}


@router.get(
    "/my-communities",
    response_model=CommunityListResponse,
    summary="List my communities",
    description=(
        "Returns a paginated list of all communities where the authenticated user "
        "is an **active member** (i.e. present in `member_users`).\n\n"
        "Communities where the user only has a **pending join request** "
        "(`requested_users`) are **not** included here.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Paginated list of the user's communities",
            "content": {
                "application/json": {
                    "example": {
                        "items": [_COMMUNITY_EXAMPLE],
                        "total": 1,
                        "page": 1,
                        "page_size": 20,
                    }
                }
            },
        },
        401: _ERROR_401,
    },
)
async def get_my_communities(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Number of items per page (max 100)"),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommunityListResponse:
    repo = CommunityRepository(db)
    items, total = await repo.get_by_member(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )
    return CommunityListResponse(
        items=[CommunityResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/{community_id}/join",
    response_model=JoinCommunityResponse,
    status_code=status.HTTP_200_OK,
    summary="Join or request to join a community",
    description=(
        "Attempt to join a community. Behaviour depends on the community type:\n\n"
        "**PUBLIC community** → user is added to `member_users` immediately. "
        "Response `status` field will be `\"joined\"`.\n\n"
        "**PRIVATE community** → user is added to `requested_users` (pending approval). "
        "Response `status` field will be `\"requested\"`. "
        "The user becomes a full member only after a moderator accepts the request "
        "(separate endpoint, coming soon).\n\n"
        "**Idempotency / conflict rules:**\n"
        "- Sending the request again when already a member → `409 Conflict`.\n"
        "- Sending the request again when a join request is already pending → `409 Conflict`.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Action completed — see `status` field for outcome",
            "content": {
                "application/json": {
                    "examples": {
                        "joined (PUBLIC)": {
                            "summary": "User joined a PUBLIC community immediately",
                            "value": {
                                "community_id": "550e8400-e29b-41d4-a716-446655440000",
                                "status": "joined",
                                "message": "You have joined the community.",
                            },
                        },
                        "requested (PRIVATE)": {
                            "summary": "Join request submitted for a PRIVATE community",
                            "value": {
                                "community_id": "550e8400-e29b-41d4-a716-446655440000",
                                "status": "requested",
                                "message": "Your join request has been sent. You will be added once a moderator approves it.",
                            },
                        },
                    }
                }
            },
        },
        401: _ERROR_401,
        404: _ERROR_404,
        409: {
            "description": "Conflict — already a member or request already pending",
            "content": {
                "application/json": {
                    "examples": {
                        "already a member": {"value": _ERROR_409_MEMBER["content"]["application/json"]["example"]},
                        "request pending": {"value": _ERROR_409_REQUESTED["content"]["application/json"]["example"]},
                    }
                }
            },
        },
    },
)
async def join_community(
    community_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JoinCommunityResponse:
    repo = CommunityRepository(db)

    community = await repo.get_by_id(community_id)
    if community is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found.",
        )

    user_id = current_user.user_id
    uid = uuid.UUID(user_id)

    # Already a member?
    if uid in community.member_users:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already a member of this community.",
        )

    if community.type == CommunityType.PUBLIC:
        await repo.add_member(community, user_id)
        return JoinCommunityResponse(
            community_id=community_id,
            status="joined",
            message="You have joined the community.",
        )

    # PRIVATE — check if request already pending
    if uid in community.requested_users:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending join request for this community.",
        )

    await repo.request_join(community, user_id)
    return JoinCommunityResponse(
        community_id=community_id,
        status="requested",
        message="Your join request has been sent. You will be added once a moderator approves it.",
    )


@router.delete(
    "/{community_id}/leave",
    response_model=LeaveCommunityResponse,
    status_code=status.HTTP_200_OK,
    summary="Leave a community",
    description=(
        "Remove the authenticated user from a community's `member_users` list.\n\n"
        "**Edge cases:**\n"
        "- If the user is not a member (including if they only have a pending join "
        "request), the request fails with `409 Conflict`. "
        "To cancel a pending join request a separate endpoint will be provided.\n"
        "- If the community does not exist, `404 Not Found` is returned.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "User successfully removed from the community",
            "content": {
                "application/json": {
                    "example": {
                        "community_id": "550e8400-e29b-41d4-a716-446655440000",
                        "message": "You have left the community.",
                    }
                }
            },
        },
        401: _ERROR_401,
        404: _ERROR_404,
        409: {
            "description": "Conflict — user is not an active member of this community",
            "content": {
                "application/json": {
                    "example": {"detail": "You are not a member of this community."}
                }
            },
        },
    },
)
async def leave_community(
    community_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeaveCommunityResponse:
    repo = CommunityRepository(db)

    community = await repo.get_by_id(community_id)
    if community is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found.",
        )

    uid = uuid.UUID(current_user.user_id)

    if uid not in community.member_users:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are not a member of this community.",
        )

    await repo.remove_member(community, current_user.user_id)
    return LeaveCommunityResponse(
        community_id=community_id,
        message="You have left the community.",
    )
