"""
Notification model.

ACID notes
----------
* ``mark_read`` and ``mark_all_read`` use ``SELECT … FOR UPDATE`` /
  ``UPDATE … WHERE`` patterns inside the open session so concurrent reads
  cannot produce double-mark races.
* ``delete`` uses a WHERE clause that includes both ``id`` and ``user_id``
  so a user can only ever delete their own notifications — no need for an
  application-layer ownership check.
* ``create_all`` in the lifespan registers the ENUM type before the table
  DDL runs, which is required by PostgreSQL.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Index, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from notification.models.base import Base


class NotificationType(str, enum.Enum):
    LIKE_POST     = "LIKE_POST"      # someone liked your post
    COMMENT_POST  = "COMMENT_POST"   # someone commented on your post
    LIKE_COMMENT  = "LIKE_COMMENT"   # someone liked your comment
    REPLY_COMMENT = "REPLY_COMMENT"  # someone replied to your comment
    JOIN_REQUEST  = "JOIN_REQUEST"   # someone requested to join your PRIVATE community
    JOIN_ACCEPTED = "JOIN_ACCEPTED"  # your join request was accepted
    NEW_POST      = "NEW_POST"       # new post in a community you follow


class Notification(Base):
    """A single notification record for one user.

    Columns
    -------
    id          — UUID primary key.
    user_id     — recipient; indexed for fast ``WHERE user_id = $1`` queries.
    type        — event category (see NotificationType enum).
    title       — short heading (≤ 255 chars).
    body        — longer description.
    data        — JSONB bag of extra context (post_id, actor_id, etc.).
                  Stored as-is and returned to the client unchanged.
    read        — False until the client calls POST /read or /read-all.
    created_at  — immutable creation timestamp.

    Indexes
    -------
    ix_notifications_user_id_created_at — covers the primary list query
        (ORDER BY created_at DESC WHERE user_id = …).
    ix_notifications_user_id_read       — covers the unread-count query
        (WHERE user_id = … AND read = false).
    """

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id_created_at", "user_id", "created_at"),
        Index("ix_notifications_user_id_read",       "user_id", "read"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    type: Mapped[NotificationType] = mapped_column(
        SAEnum(NotificationType, name="notification_type", create_type=True),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    # Arbitrary JSON payload forwarded to the client unchanged.
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
