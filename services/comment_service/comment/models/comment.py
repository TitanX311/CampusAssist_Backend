import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from comment.models.base import Base


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Cross-service UUID references — resolved via their respective services.
    post_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    community_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Self-referential parent — NULL means top-level comment, non-NULL means reply.
    parent_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Denormalised like counter — kept in sync by CommentLike insert/delete.
    likes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default="0")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class CommentLike(Base):
    """Join table — tracks which users have liked which comments.

    Composite PK (comment_id, user_id) enforces at-most-one-like-per-user at
    the database level, eliminating the need for a ``liked_by`` UUID array on
    the parent ``Comment`` row.

    ``ON DELETE CASCADE`` on the FK automatically removes all like rows when
    the parent comment is deleted, so no manual cleanup is required.
    """

    __tablename__ = "comment_likes"

    comment_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("comments.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
    )
    liked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
