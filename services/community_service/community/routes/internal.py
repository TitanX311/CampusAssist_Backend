"""
Internal cluster-only endpoints — NOT exposed via ingress.

Routes
------
GET  /internal/stats/users/{user_id}       — community count (for user_service)
GET  /internal/feed/communities/{user_id}  — member community IDs (for my-feed)
GET  /internal/feed/public-community-ids   — all PUBLIC community IDs (India feed)
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from community.config.database import get_db
from community.models.community import Community, CommunityMember, CommunityType

router = APIRouter(prefix="/internal", tags=["Internal"])


# ---------------------------------------------------------------------------
# Stats — consumed by user_service
# ---------------------------------------------------------------------------

@router.get("/stats/users/{user_id}", include_in_schema=False)
async def user_community_count(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the number of communities that *user_id* is a member of."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        return {"count": 0}

    result = await db.execute(
        select(func.count())
        .select_from(CommunityMember)
        .where(CommunityMember.user_id == uid)
    )
    count = result.scalar_one_or_none() or 0
    return {"count": int(count)}


# ---------------------------------------------------------------------------
# Feed — my-feed (personalised, per-user)
# ---------------------------------------------------------------------------

@router.get("/feed/communities/{user_id}", include_in_schema=False)
async def user_feed_communities(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return all community IDs the user is a member of.

    Called by feed_service to determine which communities to pull posts from
    when building a personalised feed.

    Returns: ``{"community_ids": ["id1", "id2", ...]}``
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        return {"community_ids": []}

    result = await db.execute(
        select(CommunityMember.community_id).where(CommunityMember.user_id == uid)
    )
    return {"community_ids": [str(row) for row in result.scalars().all()]}


# ---------------------------------------------------------------------------
# Feed — India feed (public communities, all colleges)
# ---------------------------------------------------------------------------

@router.get("/feed/public-community-ids", include_in_schema=False)
async def public_community_ids(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return all PUBLIC community IDs across every college.

    Called by feed_service to build the Across-India trending feed.
    Only PUBLIC communities are included — PRIVATE communities and their posts
    are never surfaced in the shared discovery feed.

    Returns: ``{"community_ids": ["id1", "id2", ...]}``
    """
    result = await db.execute(
        select(Community.id).where(Community.type == CommunityType.PUBLIC)
    )
    return {"community_ids": [str(row) for row in result.scalars().all()]}
