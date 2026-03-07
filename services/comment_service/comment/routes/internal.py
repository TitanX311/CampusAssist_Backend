"""
Internal stats endpoint for user_service consumption.

NOT exposed via ingress — accessed only from within the cluster at:
  http://comment-service/internal/stats/users/{user_id}

Returns the number of comments authored by the given user.
No authentication required (cluster-internal only).
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from comment.config.database import get_db
from comment.models.comment import Comment

router = APIRouter(prefix="/internal", tags=["Internal"])


@router.get("/stats/users/{user_id}", include_in_schema=False)
async def user_comment_count(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the total number of comments created by *user_id*."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        return {"count": 0}

    result = await db.execute(
        select(func.count()).select_from(Comment).where(Comment.user_id == uid)
    )
    count = result.scalar_one_or_none() or 0
    return {"count": int(count)}
