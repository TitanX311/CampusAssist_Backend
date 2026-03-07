import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from post.models.base import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Cross-service UUID references — resolved via their respective services.
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    community_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Denormalized counters kept in sync atomically.
    # ``likes`` is bumped/decremented via UPDATE … SET likes = likes ± 1 in the
    # same transaction as the PostLike join table insert/delete.
    likes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default="0")
    views: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default="0")

    # Cross-service UUID arrays (attachments and comments belong to other services)
    attachments: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, default=list, server_default="{}"
    )
    comments: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, default=list, server_default="{}"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class PostLike(Base):
    """Join table: which users have liked which posts.

    ACID notes
    ----------
    * Composite primary key ``(post_id, user_id)`` enforces uniqueness at the
      DB level — concurrent likes cannot produce duplicate rows.
    * Writers use ``INSERT … ON CONFLICT DO NOTHING`` with ``RETURNING`` to
      detect whether a row was actually inserted before bumping the counter.
    * Unlike / unlike operations delete the row and decrement the counter in
      the same transaction.  ``func.greatest(likes - 1, 0)`` ensures the
      counter never goes negative.
    * ON DELETE CASCADE keeps the table clean when a post is deleted.
    """

    __tablename__ = "post_likes"

    post_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("posts.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True
    )
    liked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

