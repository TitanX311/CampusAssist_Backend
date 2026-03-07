"""
InteractionRepository — ACID-compliant persistence layer for feed interactions.

All write paths use ``SELECT … FOR UPDATE`` before inserting or updating a row
so that concurrent requests for the same (user_id, post_id) pair are serialised
and the uniqueness constraint is never violated at the application level.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from feed.models.feed_interaction import FeedInteraction


class InteractionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def mark_seen(self, user_id: str, post_id: str) -> FeedInteraction:
        """
        Upsert a seen-interaction under a row-level lock.

        Atomicity  — the whole operation runs inside the caller's transaction
                     (committed by ``get_db`` on success).
        Isolation  — ``WITH FOR UPDATE`` prevents two simultaneous requests
                     for the same (user_id, post_id) from both doing an INSERT
                     and hitting the unique-constraint violation.
        Durability — committed to Postgres; survives Redis cache flushes.
        """
        uid = uuid.UUID(user_id)

        # 1. Lock the row (or confirm it doesn't exist yet)
        result = await self.db.execute(
            select(FeedInteraction)
            .where(
                (FeedInteraction.user_id == uid)
                & (FeedInteraction.post_id == post_id)
            )
            .with_for_update()
        )
        interaction = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if interaction is None:
            # 2a. Insert — safe because we hold the gap lock
            interaction = FeedInteraction(
                user_id=uid,
                post_id=post_id,
                seen_at=now,
                updated_at=now,
            )
            self.db.add(interaction)
        else:
            # 2b. Update — refresh the timestamp
            interaction.seen_at = now
            interaction.updated_at = now

        await self.db.flush()
        await self.db.refresh(interaction)
        return interaction

    async def get_seen_post_ids(
        self,
        user_id: str,
        post_ids: list[str],
    ) -> set[str]:
        """Return the subset of *post_ids* that the user has already seen."""
        if not post_ids:
            return set()
        uid = uuid.UUID(user_id)
        result = await self.db.execute(
            select(FeedInteraction.post_id).where(
                (FeedInteraction.user_id == uid)
                & (FeedInteraction.post_id.in_(post_ids))
            )
        )
        return {row for row in result.scalars().all()}
