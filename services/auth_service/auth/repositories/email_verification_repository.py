from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.config.settings import get_settings
from auth.models.email_verification import EmailVerificationToken


class EmailVerificationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: str) -> EmailVerificationToken:
        """
        Create a fresh verification token for *user_id*.

        Any existing (unused, unexpired) tokens for the same user are deleted
        first so there is never more than one live token per user.
        """
        settings = get_settings()
        # Purge old tokens for this user before creating a new one.
        await self.db.execute(
            delete(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user_id
            )
        )
        token = EmailVerificationToken(
            user_id=user_id,
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES),
        )
        self.db.add(token)
        await self.db.flush()
        await self.db.refresh(token)
        return token

    async def get_by_token(self, token: str) -> EmailVerificationToken | None:
        result = await self.db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token == token
            )
        )
        return result.scalar_one_or_none()

    async def mark_used(self, record: EmailVerificationToken) -> None:
        record.used = True
        await self.db.flush()

    async def delete_expired(self) -> None:
        """Housekeeping — remove all tokens past their expiry time."""
        await self.db.execute(
            delete(EmailVerificationToken).where(
                EmailVerificationToken.expires_at < datetime.now(timezone.utc)
            )
        )
        await self.db.flush()
