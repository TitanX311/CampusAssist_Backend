import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Enum as SAEnum, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from college.models import Base

if TYPE_CHECKING:
    from auth.models.user import User  # noqa: F401
    from college.models.community import Community  # noqa: F401


# association tables for many-to-many relations
college_admins = Table(
    "college_admins",
    Base.metadata,
    Column("college_id", String, ForeignKey("colleges.id"), primary_key=True),
    Column("user_id", String, ForeignKey("users.id"), primary_key=True),
)

college_communities = Table(
    "college_communities",
    Base.metadata,
    Column("college_id", String, ForeignKey("colleges.id"), primary_key=True),
    Column("community_id", String, ForeignKey("communities.id"), primary_key=True),
)


class CollegeType(str, enum.Enum):
    PRIVATE = "PRIVATE"
    PUBLIC = "PUBLIC"
    FUNDED = "FUNDED"
    OTHER = "OTHER"


class College(Base):
    __tablename__ = "colleges"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    contact_email: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    type: Mapped[CollegeType] = mapped_column(
        SAEnum(CollegeType, name="college_type"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    admin_users: Mapped[list["User"]] = relationship(
        "User",
        secondary=college_admins,
        back_populates="admin_colleges",
    )

    communities: Mapped[list["Community"]] = relationship(
        "Community",
        secondary=college_communities,
        back_populates="colleges",
    )
