"""
Internal cluster-only endpoints — NOT exposed via ingress.

Routes
------
GET  /internal/stats/users/{user_id}    — post count (for user_service)
GET  /internal/feed/posts               — recent posts by community (for my-feed)
POST /internal/feed/trending-posts      — top-engaged posts from many communities
                                           in a single DB query (for India feed)
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from post.config.database import get_db
from post.models.post import Post

router = APIRouter(prefix="/internal", tags=["Internal"])


@router.get("/stats/users/{user_id}", include_in_schema=False)
async def user_post_count(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the total number of posts created by *user_id*."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        return {"count": 0}

    result = await db.execute(
        select(func.count()).select_from(Post).where(Post.user_id == uid)
    )
    count = result.scalar_one_or_none() or 0
    return {"count": int(count)}


@router.get("/feed/posts", include_in_schema=False)
async def feed_posts_by_community(
    community_id: str,
    since_hours: int = 168,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Return recent posts from a single community for feed_service.

    Fetches posts created within the last *since_hours* hours (default 7 days),
    ordered newest-first, capped at *limit* rows.

    Returns a lightweight dict with all fields needed for feed scoring:
    likes, views, comment_count (len of comments array), created_at.

    NOT authenticated — cluster-internal only.
    """
    try:
        cid = uuid.UUID(community_id)
    except ValueError:
        return {"posts": []}

    since_dt = datetime.now(timezone.utc) - timedelta(hours=max(1, since_hours))

    result = await db.execute(
        select(Post)
        .where((Post.community_id == cid) & (Post.created_at >= since_dt))
        .order_by(Post.created_at.desc())
        .limit(min(limit, 200))
    )
    posts = result.scalars().all()

    return {
        "posts": [
            {
                "post_id": p.id,
                "community_id": str(p.community_id),
                "user_id": str(p.user_id),
                "content": p.content,
                "likes": p.likes,
                "views": p.views,
                "comment_count": len(p.comments),
                "attachments": [str(a) for a in p.attachments],
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
            }
            for p in posts
        ]
    }


# ---------------------------------------------------------------------------
# Trending posts — India feed (bulk, engagement-sorted)
# ---------------------------------------------------------------------------

class _TrendingRequest(BaseModel):
    community_ids: list[str]
    since_hours: int = Field(default=168, ge=0)
    limit: int = Field(default=200, ge=1, le=500)
    # Minimum engagement score (likes×5 + comments×3) a post must have.
    # Set > 0 for the India feed to exclude zero-engagement posts.
    min_engagement: int = Field(default=0, ge=0)


@router.post("/feed/trending-posts", include_in_schema=False)
async def trending_posts(
    body: _TrendingRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the most-engaged posts from a set of communities in one query.

    Ordered by engagement score (likes×5 + comments×3 + views×0.1) DESC.
    Posts whose engagement score < *min_engagement* are excluded — this lets
    the India feed filter out zero-engagement content in a single DB round-trip.

    When *since_hours* = 0, no time filter is applied (all-time trending).

    NOT authenticated — cluster-internal only.
    """
    if not body.community_ids:
        return {"posts": []}

    try:
        cids = [uuid.UUID(c) for c in body.community_ids]
    except ValueError:
        return {"posts": []}

    # Engagement score computed in SQL so Postgres sorts before rows are transferred.
    engagement_score = (
        Post.likes * 5
        + func.coalesce(func.array_length(Post.comments, 1), 0) * 3
        + Post.views * 0.1
    )

    conditions = [Post.community_id.in_(cids)]

    if body.since_hours > 0:
        since_dt = datetime.now(timezone.utc) - timedelta(hours=body.since_hours)
        conditions.append(Post.created_at >= since_dt)

    if body.min_engagement > 0:
        conditions.append(engagement_score >= body.min_engagement)

    result = await db.execute(
        select(Post)
        .where(*conditions)
        .order_by(engagement_score.desc())
        .limit(min(body.limit, 500))
    )
    posts = result.scalars().all()

    return {
        "posts": [
            {
                "post_id": p.id,
                "community_id": str(p.community_id),
                "user_id": str(p.user_id),
                "content": p.content,
                "likes": p.likes,
                "views": p.views,
                "comment_count": len(p.comments),
                "attachments": [str(a) for a in p.attachments],
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
            }
            for p in posts
        ]
    }