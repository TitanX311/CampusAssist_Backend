"""
Feed routes — only accessible to users of type ``USER``.

Route overview
--------------
GET  /api/feed/my                    — personalised feed (communities user joined)
GET  /api/feed/india                 — Across-India trending feed (public communities)
GET  /api/feed                       — alias for /api/feed/my (backward-compat)
POST /api/feed/seen/{post_id}        — mark a post as seen (Redis + Postgres)
DELETE /api/feed/cache               — force rebuild of the user's my-feed cache
DELETE /api/feed/india/cache         — force rebuild of the shared India feed cache

My Feed
-------
Personalised, recency-first.  Posts are pulled from every community the
authenticated user is a member of (including PRIVATE ones).  Score formula:

  10 × (1 - age_h / window_h)  +  likes×3 + comments×2 + views×0.05

Cache is per-user (Redis key = ``feed:v1:{user_id}``), TTL = FEED_CACHE_TTL_SECONDS.

Across-India Feed
-----------------
Shared discovery feed, engagement-first.  Posts are pulled from ALL PUBLIC
communities across every college.  Score formula:

  likes×5 + comments×3 + views×0.1  +  3 × (1 - age_h / india_window_h)

Cache is shared across all users (Redis key = ``feed:v1:india``),
TTL = INDIA_FEED_CACHE_TTL_SECONDS (default 10 min).

Seen state and cursor pagination apply to the My Feed only.  The India feed
is a simple window of the top N posts — it doesn't track per-user seen state
since it is a discovery surface, not a personal timeline.

Cursor-based pagination
-----------------------
The feed list is stored as a flat ranked list in Redis.  The cursor is the
integer index of the first item on the next page (e.g. ``"20"`` means skip
the first 20 items).  Clients pass ``?cursor=20`` to get page 2.
``next_cursor`` is ``null`` when there are no more items.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from feed import cache
from feed.config.database import get_db
from feed.config.settings import get_settings
from feed.dependencies.auth import TokenPayload, get_current_user
from feed.engine import build_feed, build_india_feed
from feed.repositories import InteractionRepository
from feed.schemas import (
    FeedItem,
    FeedResponse,
    IndiaFeedItem,
    IndiaFeedResponse,
    InvalidateCacheResponse,
    SeenResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feed", tags=["Feed"])


# ---------------------------------------------------------------------------
# Guard helper
# ---------------------------------------------------------------------------

def _require_user(current_user: TokenPayload) -> TokenPayload:
    """Raise 403 if the caller is not a regular USER."""
    if current_user.user_type != "USER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Feed is only available to accounts of type USER. "
                f"Your account type is {current_user.user_type!r}."
            ),
        )
    return current_user


# ---------------------------------------------------------------------------
# GET /api/feed/my  — personalised My Feed
# ---------------------------------------------------------------------------

@router.get(
    "/my",
    response_model=FeedResponse,
    summary="Get My Feed (personalised)",
    description=(
        "Returns a ranked, paginated feed of posts from **every community the "
        "authenticated user is a member of** (both PUBLIC and PRIVATE).\n\n"
        "**Two-tier ordering:**\n"
        "- **Section 1 — Recent** (last 24 h): sorted newest-first so you always "
        "see what is happening right now.\n"
        "- **Section 2 — Popular** (older posts): sorted by engagement "
        "(`likes×3 + comments×2`) so the best content from the past week surfaces "
        "after you have caught up on today's posts.\n\n"
        "Already-seen posts are filtered from the returned items but kept in the "
        "cache so pagination cursors remain stable.\n\n"
        "Use `next_cursor` as `?cursor=` on the next request.\n\n"
        "**Only accessible to accounts with `user_type = USER`.**\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {"description": "Paginated My Feed"},
        401: {"description": "Missing / invalid token"},
        403: {"description": "Account type is not USER"},
    },
)
async def get_my_feed(
    cursor: int = Query(default=0, ge=0, description="Pagination cursor (item index)"),
    page_size: int = Query(default=20, ge=1, le=50, description="Items per page"),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FeedResponse:
    _require_user(current_user)

    user_id = current_user.user_id
    settings = get_settings()
    built_fresh = False

    # 1. Try Redis cache
    cached = await cache.get_cached_feed(user_id)
    if cached is None:
        logger.info("My Feed cache miss for user %s — building fresh", user_id)
        raw_posts = await build_feed(user_id)
        built_fresh = True

        # Seed seen set from Postgres on cold start so history survives Redis flush
        all_post_ids = [p["post_id"] for p in raw_posts]
        db_seen = await InteractionRepository(db).get_seen_post_ids(user_id, all_post_ids)
        if db_seen:
            await cache.mark_seen_bulk(user_id, list(db_seen))

        await cache.set_cached_feed(user_id, raw_posts, ttl=settings.FEED_CACHE_TTL_SECONDS)
        cached = raw_posts

    # 2. Load seen set and paginate
    redis_seen = await cache.get_seen_ids(user_id)
    total_in_cache = len(cached)

    paginated_raw = cached[cursor: cursor + page_size]
    next_cursor: int | None = (
        cursor + page_size if (cursor + page_size) < total_in_cache else None
    )

    items = []
    for p in paginated_raw:
        post_id = p.get("post_id") or p.get("id", "")
        items.append(
            FeedItem(
                post_id=post_id,
                community_id=p.get("community_id", ""),
                user_id=p.get("user_id", ""),
                content=p.get("content", ""),
                likes=p.get("likes", 0),
                views=p.get("views", 0),
                comment_count=p.get("comment_count", 0),
                attachments=p.get("attachments", []),
                score=p.get("score", 0.0),
                created_at=p.get("created_at"),
                seen=post_id in redis_seen,
            )
        )

    return FeedResponse(
        items=items,
        next_cursor=str(next_cursor) if next_cursor is not None else None,
        total_in_cache=total_in_cache,
        built_fresh=built_fresh,
    )


# ---------------------------------------------------------------------------
# GET /api/feed  — backward-compatible alias for /api/feed/my
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=FeedResponse,
    summary="Get personalised feed (alias for /api/feed/my)",
    description="Alias for `GET /api/feed/my` kept for backward compatibility.",
    include_in_schema=False,
)
async def get_feed_alias(
    cursor: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=50),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FeedResponse:
    return await get_my_feed(
        cursor=cursor,
        page_size=page_size,
        current_user=current_user,
        db=db,
    )


# ---------------------------------------------------------------------------
# GET /api/feed/india  — Across-India trending feed
# ---------------------------------------------------------------------------

@router.get(
    "/india",
    response_model=IndiaFeedResponse,
    summary="Get Across-India Feed (trending public communities)",
    description=(
        "Returns the most-engaged posts from **all PUBLIC communities across every "
        "college** — a shared recommendation surface for the whole platform.\n\n"
        "**Pure engagement ranking (no recency factor):**\n"
        "```\n"
        "score = likes × 5 + comments × 3 + views × 0.1\n"
        "```\n\n"
        "Only posts with **real engagement** (score ≥ threshold) are included — "
        "zero-engagement posts are filtered out so this surface always shows "
        "content the community has already validated.\n\n"
        "The feed is cached in a **single shared Redis key** (not per-user) "
        "with a 10-minute TTL. All users see the same ranked list.\n\n"
        "Private communities are **never** included.\n\n"
        "Use `next_cursor` as `?cursor=` on the next request.\n\n"
        "**Only accessible to accounts with `user_type = USER`.**\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {"description": "Paginated Across-India feed"},
        401: {"description": "Missing / invalid token"},
        403: {"description": "Account type is not USER"},
    },
)
async def get_india_feed(
    cursor: int = Query(default=0, ge=0, description="Pagination cursor (item index)"),
    page_size: int = Query(default=20, ge=1, le=50, description="Items per page"),
    current_user: TokenPayload = Depends(get_current_user),
) -> IndiaFeedResponse:
    _require_user(current_user)

    settings = get_settings()
    built_fresh = False

    # 1. Try shared Redis cache
    cached = await cache.get_cached_india_feed()
    if cached is None:
        logger.info("India Feed cache miss — building fresh")
        cached = await build_india_feed()
        built_fresh = True
        await cache.set_cached_india_feed(cached, ttl=settings.INDIA_FEED_CACHE_TTL_SECONDS)

    total_in_cache = len(cached)
    paginated_raw = cached[cursor: cursor + page_size]
    next_cursor: int | None = (
        cursor + page_size if (cursor + page_size) < total_in_cache else None
    )

    items = [
        IndiaFeedItem(
            post_id=p.get("post_id") or p.get("id", ""),
            community_id=p.get("community_id", ""),
            user_id=p.get("user_id", ""),
            content=p.get("content", ""),
            likes=p.get("likes", 0),
            views=p.get("views", 0),
            comment_count=p.get("comment_count", 0),
            attachments=p.get("attachments", []),
            score=p.get("score", 0.0),
            created_at=p.get("created_at"),
        )
        for p in paginated_raw
    ]

    return IndiaFeedResponse(
        items=items,
        next_cursor=str(next_cursor) if next_cursor is not None else None,
        total_in_cache=total_in_cache,
        built_fresh=built_fresh,
    )


# ---------------------------------------------------------------------------
# POST /api/feed/seen/{post_id}
# ---------------------------------------------------------------------------

@router.post(
    "/seen/{post_id}",
    response_model=SeenResponse,
    summary="Mark a post as seen",
    description=(
        "Record that the authenticated user has seen *post_id*.\n\n"
        "**Dual-write:** persisted to Postgres under `SELECT … FOR UPDATE` "
        "(ACID) **and** added to the Redis seen-set.  "
        "Also invalidates the user's My Feed cache so the seen post is "
        "excluded on the next `GET /api/feed/my`.\n\n"
        "**Only accessible to accounts with `user_type = USER`.**\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {"description": "Post marked as seen"},
        401: {"description": "Missing / invalid token"},
        403: {"description": "Account type is not USER"},
    },
)
async def mark_seen(
    post_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SeenResponse:
    _require_user(current_user)
    user_id = current_user.user_id

    await InteractionRepository(db).mark_seen(user_id, post_id)
    await cache.mark_seen(user_id, post_id)
    await cache.invalidate_feed(user_id)

    return SeenResponse(post_id=post_id)


# ---------------------------------------------------------------------------
# DELETE /api/feed/cache  — invalidate user's My Feed cache
# ---------------------------------------------------------------------------

@router.delete(
    "/cache",
    response_model=InvalidateCacheResponse,
    summary="Invalidate My Feed cache",
    description=(
        "Force a fresh My Feed rebuild on the next `GET /api/feed/my`.\n\n"
        "Useful after creating or interacting with a post.\n\n"
        "**Only accessible to accounts with `user_type = USER`.**\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {"description": "My Feed cache invalidated"},
        401: {"description": "Missing / invalid token"},
        403: {"description": "Account type is not USER"},
    },
)
async def invalidate_cache(
    current_user: TokenPayload = Depends(get_current_user),
) -> InvalidateCacheResponse:
    _require_user(current_user)
    await cache.invalidate_feed(current_user.user_id)
    return InvalidateCacheResponse()


# ---------------------------------------------------------------------------
# DELETE /api/feed/india/cache  — invalidate shared India feed cache
# ---------------------------------------------------------------------------

@router.delete(
    "/india/cache",
    response_model=InvalidateCacheResponse,
    summary="Invalidate Across-India Feed cache",
    description=(
        "Force a fresh India feed rebuild on the next `GET /api/feed/india`.\n\n"
        "Useful after a new post goes viral or for admin-triggered refreshes.\n\n"
        "**Only accessible to accounts with `user_type = USER`.**\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {"description": "India Feed cache invalidated"},
        401: {"description": "Missing / invalid token"},
        403: {"description": "Account type is not USER"},
    },
)
async def invalidate_india_cache(
    current_user: TokenPayload = Depends(get_current_user),
) -> InvalidateCacheResponse:
    _require_user(current_user)
    await cache.invalidate_india_feed()
    return InvalidateCacheResponse(status="india feed cache invalidated")
