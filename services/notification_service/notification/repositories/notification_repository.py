"""
Notification repository.

ACID guarantees
---------------
* ``create``        — plain INSERT, flushed inside the open session.
* ``mark_read``     — SELECT … FOR UPDATE before the UPDATE so concurrent
                      requests for the same notification are serialised at
                      the DB level (prevents double-mark races).
* ``mark_all_read`` — single UPDATE … WHERE (user_id, read=false) batches all
                      unread rows in one statement.
* ``delete``        — WHERE clause includes user_id so a user can never
                      delete someone else's notification.
All mutations call ``flush()`` inside the session; ``commit`` / ``rollback``
is handled by the ``get_db`` FastAPI dependency.
"""

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import delete as sql_delete
from sqlalchemy import func, select
from sqlalchemy import update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from notification.models.notification import Notification, NotificationType


class NotificationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create(
        self,
        user_id: str,
        type: str,
        title: str,
        body: str,
        data: dict | str | None = None,
    ) -> Notification:
        """Persist a new notification.

        *data* may be a dict or a JSON string (for callers that receive raw
        JSON from a gRPC field).
        """
        if isinstance(data, str) and data:
            try:
                data = json.loads(data)
            except (ValueError, TypeError):
                data = None

        n = Notification(
            user_id=uuid.UUID(user_id),
            type=NotificationType(type),
            title=title,
            body=body,
            data=data or None,
        )
        self.db.add(n)
        await self.db.flush()
        await self.db.refresh(n)
        return n

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def get_by_user(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
    ) -> tuple[list[Notification], int]:
        """Return paginated notifications for a user, newest first."""
        uid = uuid.UUID(user_id)
        conditions = [Notification.user_id == uid]
        if unread_only:
            conditions.append(Notification.read.is_(False))

        total = (
            await self.db.execute(
                select(func.count())
                .select_from(Notification)
                .where(*conditions)
            )
        ).scalar_one()

        items = (
            await self.db.execute(
                select(Notification)
                .where(*conditions)
                .order_by(Notification.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()

        return list(items), total

    async def get_by_id(
        self, notification_id: uuid.UUID, user_id: str
    ) -> Notification | None:
        uid = uuid.UUID(user_id)
        return (
            await self.db.execute(
                select(Notification).where(
                    Notification.id == notification_id,
                    Notification.user_id == uid,
                )
            )
        ).scalar_one_or_none()

    async def get_unread_count(self, user_id: str) -> int:
        uid = uuid.UUID(user_id)
        return (
            await self.db.execute(
                select(func.count())
                .select_from(Notification)
                .where(
                    Notification.user_id == uid,
                    Notification.read.is_(False),
                )
            )
        ).scalar_one()

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    async def mark_read(
        self, notification_id: uuid.UUID, user_id: str
    ) -> Notification | None:
        """Mark a single notification as read (SELECT … FOR UPDATE guard)."""
        uid = uuid.UUID(user_id)
        n = (
            await self.db.execute(
                select(Notification)
                .where(
                    Notification.id == notification_id,
                    Notification.user_id == uid,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()

        if n is None:
            return None
        if not n.read:
            n.read = True
            await self.db.flush()
            await self.db.refresh(n)
        return n

    async def mark_all_read(self, user_id: str) -> int:
        """Mark all unread notifications for a user as read.

        Returns the number of rows updated.
        """
        uid = uuid.UUID(user_id)
        result = await self.db.execute(
            sql_update(Notification)
            .where(Notification.user_id == uid, Notification.read.is_(False))
            .values(read=True)
            .returning(Notification.id)
        )
        await self.db.flush()
        return len(result.fetchall())

    async def delete(self, notification_id: uuid.UUID, user_id: str) -> bool:
        """Delete a notification owned by *user_id*.

        Returns True if a row was deleted, False if it did not exist or
        belongs to a different user.
        """
        uid = uuid.UUID(user_id)
        result = await self.db.execute(
            sql_delete(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == uid,
            )
            .returning(Notification.id)
        )
        await self.db.flush()
        return result.scalar_one_or_none() is not None
