import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.config.settings import get_settings
from auth.models.refresh_token import RefreshToken

settings = get_settings()


class RefreshTokenRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: str) -> RefreshToken:
        refresh_token = RefreshToken(
            token=secrets.token_urlsafe(64),
            user_id=user_id,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(refresh_token)
        await self.db.flush()
        await self.db.refresh(refresh_token)
        return refresh_token

    async def get_by_token(self, token: str) -> RefreshToken | None:
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token == token)
        )
        return result.scalar_one_or_none()

    async def revoke(self, refresh_token: RefreshToken) -> None:
        refresh_token.revoked = True
        await self.db.flush()
