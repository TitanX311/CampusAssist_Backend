from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.google_id == google_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        google_id: str,
        email: str,
        name: str | None = None,
        picture: str | None = None,
    ) -> User:
        user = User(google_id=google_id, email=email, name=name, picture=picture)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update_profile(
        self,
        user: User,
        name: str | None,
        picture: str | None,
    ) -> User:
        if name is not None:
            user.name = name
        if picture is not None:
            user.picture = picture
        user.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(user)
        return user
