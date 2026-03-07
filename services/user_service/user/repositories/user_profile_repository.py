"""
UserProfileRepository — ACID-safe persistence for user profile caches.

All mutation paths use ``get_by_id_for_update`` (SELECT … FOR UPDATE) so
that concurrent requests for the same user serialise instead of racing.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from user.models.user_profile import UserProfile


class UserProfileRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    async def get_by_id(self, user_id: str) -> UserProfile | None:
        """Non-locking read — safe for plain GET without mutation."""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, user_id: str) -> UserProfile | None:
        """
        Locking read (SELECT … FOR UPDATE).

        Use this at the start of any write path to prevent lost updates when
        two concurrent requests try to refresh the same user's cache.
        """
        result = await self.db.execute(
            select(UserProfile)
            .where(UserProfile.user_id == user_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Writes (all callers must hold a FOR UPDATE lock first)
    # ------------------------------------------------------------------

    async def upsert(
        self,
        *,
        user_id: str,
        email: str | None,
        name: str | None,
        picture: str | None,
        user_type: str,
        is_active: bool,
        joined_at: datetime | None,
        post_count: int,
        comment_count: int,
        community_count: int,
    ) -> UserProfile:
        """
        Insert-or-update the cached profile for *user_id*.

        ACID note: the caller is expected to have called ``get_by_id_for_update``
        beforehand so the row is locked for the duration of this transaction.
        We use a non-locking read here to avoid a redundant second lock request
        on the same row within the same transaction.
        """
        now = datetime.now(timezone.utc)

        # Non-locking re-read — caller already holds the FOR UPDATE lock.
        existing = await self.get_by_id(user_id)
        if existing is None:
            profile = UserProfile(
                user_id=user_id,
                email=email,
                name=name,
                picture=picture,
                user_type=user_type,
                is_active=is_active,
                joined_at=joined_at,
                post_count=post_count,
                comment_count=comment_count,
                community_count=community_count,
                last_synced_at=now,
                updated_at=now,
            )
            self.db.add(profile)
        else:
            existing.email = email
            existing.name = name
            existing.picture = picture
            existing.user_type = user_type
            existing.is_active = is_active
            existing.joined_at = joined_at
            existing.post_count = post_count
            existing.comment_count = comment_count
            existing.community_count = community_count
            existing.last_synced_at = now
            existing.updated_at = now
            profile = existing

        await self.db.flush()
        await self.db.refresh(profile)
        return profile
