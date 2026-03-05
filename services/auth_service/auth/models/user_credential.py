import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auth.models.base import Base

if TYPE_CHECKING:
    from auth.models.user import User


class AuthProvider(str, enum.Enum):
    EMAIL = "email"
    GOOGLE = "google"


class UserCredential(Base):
    """
    Stores one row per authentication method per user.

    - Google OAuth  → provider=GOOGLE, provider_user_id=<google 'sub'>, password_hash=NULL
    - Email/password → provider=EMAIL,  provider_user_id=<email address>, password_hash=<bcrypt hash>
    """

    __tablename__ = "user_credentials"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[AuthProvider] = mapped_column(
        SAEnum(AuthProvider, name="auth_provider"), nullable=False
    )
    # Google: the Google 'sub' value.  Email: the user's email address.
    provider_user_id: Mapped[str] = mapped_column(
        String, nullable=False, index=True
    )
    # Only populated for the EMAIL provider.
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship("User", back_populates="credentials")

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_user_id",
            name="uq_credential_provider_user_id",
        ),
    )
