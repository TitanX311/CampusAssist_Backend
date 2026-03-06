import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from auth.models.base import Base


class EmailVerificationToken(Base):
    """
    Single-use token for verifying an email address.

    Created after email/password registration. The token is sent to the user
    via email; the user clicks the link which calls POST /api/auth/email/verify.

    Tokens expire after EMAIL_VERIFICATION_EXPIRE_MINUTES minutes (default 24 h).
    After use the `used` flag is set to True so the token cannot be replayed.
    Google OAuth users are verified immediately and never receive one of these.
    """

    __tablename__ = "email_verification_tokens"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # URL-safe random token sent in the verification link.
    token: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True,
        default=lambda: secrets.token_urlsafe(32),
    )
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
