import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from community.models.base import Base


class CommunityType(str, enum.Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


class Community(Base):
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

    # Cross-service UUID references — stored as native Postgres UUID arrays.
    # Actual user/college/post objects are resolved via their respective services.
    member_users: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, default=list, server_default="{}"
    )
    requested_users: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, default=list, server_default="{}"
    )
    parent_colleges: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, default=list, server_default="{}"
    )
    posts: Mapped[list[uuid.UUID]] = mapped_column(
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
