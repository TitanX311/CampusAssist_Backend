import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from community.models.base import Base


class CommunityType(str, enum.Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


class Community(Base):
    """Core community entity.

    ACID notes
    ----------
    * ``member_users`` / ``requested_users`` arrays are **removed** in favour of
      the normalised ``CommunityMember`` / ``CommunityJoinRequest`` join tables
      below, which support proper row-level locking and avoid lost-update races.
    * ``parent_colleges`` / ``posts`` remain as UUID arrays because they are
      cross-service references owned by other domains.
    * ``member_count`` and ``post_count`` are *denormalised counters* updated
      atomically (via ``UPDATE … SET count = count ± 1``) so list endpoints never
      need a COUNT subquery.  They can drift only on unhandled crashes — the gRPC
      servicer and repository always use the join tables as the source of truth
      for membership decisions.
    """

    __tablename__ = "communities"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    type: Mapped[CommunityType] = mapped_column(
        SAEnum(CommunityType, name="community_type"),
        nullable=False,
        default=CommunityType.PUBLIC,
    )

    # Cross-service UUID references — stored as Postgres UUID arrays.
    # These belong to other domains, so we keep them as arrays.
    parent_colleges: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, default=list, server_default="{}"
    )
    posts: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, default=list, server_default="{}"
    )

    # Denormalised counters — kept in sync by the repository (same transaction).
    # Source-of-truth for membership is the CommunityMember join table.
    member_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    post_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class CommunityMember(Base):
    """Join table: which users are active members of which community.

    ACID notes
    ----------
    * Composite primary key ``(community_id, user_id)`` enforces uniqueness at
      the DB level — concurrent joins cannot produce duplicate rows.
    * Writers use ``INSERT … ON CONFLICT DO NOTHING`` so the operation is always
      idempotent without needing a prior SELECT.
    * Deletes are plain single-row deletes — no array deserialization race.
    """

    __tablename__ = "community_members"

    community_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("communities.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class CommunityJoinRequest(Base):
    """Join table: pending join requests for PRIVATE communities.

    ACID notes
    ----------
    * Same composite-PK uniqueness guarantee as CommunityMember.
    * An approve/reject operation deletes from this table and (for approve)
      inserts into CommunityMember within the same transaction.
    """

    __tablename__ = "community_join_requests"

    community_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("communities.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
