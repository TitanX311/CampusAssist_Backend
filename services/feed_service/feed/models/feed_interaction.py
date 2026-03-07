import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class FeedInteraction(Base):
    """
    Durable, ACID-compliant record of which posts a user has seen.

    Redis holds a TTL-based set for fast reads; this table is the ground-truth
    store so that "seen" state survives Redis flushes / restarts.

    Write path:
        - All upserts use ``SELECT … FOR UPDATE`` via
          ``InteractionRepository.mark_seen`` to serialise concurrent requests
          for the same (user_id, post_id) pair and prevent duplicate rows.
        - ``get_db`` commits on success and rolls back on any exception.
    """

    __tablename__ = "feed_interactions"
    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="uq_feed_user_post"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    post_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
