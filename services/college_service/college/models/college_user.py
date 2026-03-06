"""
CollegeUser — cross-service join table.

Tracks every user who is a member of at least one community that belongs to
a given college.  Populated/pruned automatically via gRPC calls from
community_service when users join or leave communities.

Composite primary key (college_id, user_id) ensures uniqueness — a user
appears at most once per college regardless of how many communities they
joined within that college.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from college.models.base import Base


class CollegeUser(Base):
    __tablename__ = "college_users"
    __table_args__ = (
        UniqueConstraint("college_id", "user_id", name="uq_college_user"),
    )

    college_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
