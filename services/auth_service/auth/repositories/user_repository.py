from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models.user import User
from auth.models.user_credential import AuthProvider, UserCredential


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # User look-ups
    # ------------------------------------------------------------------

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Credential look-ups
    # ------------------------------------------------------------------

    async def get_credential_by_google_id(
        self, google_id: str
    ) -> UserCredential | None:
        """Return the Google OAuth credential row for the given Google 'sub'."""
        result = await self.db.execute(
            select(UserCredential).where(
                UserCredential.provider == AuthProvider.GOOGLE,
                UserCredential.provider_user_id == google_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_credential_by_email_provider(
        self, email: str
    ) -> UserCredential | None:
        """Return the email/password credential row for the given email address."""
        result = await self.db.execute(
            select(UserCredential).where(
                UserCredential.provider == AuthProvider.EMAIL,
                UserCredential.provider_user_id == email,
            )
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # User creation (one method per auth provider)
    # ------------------------------------------------------------------

    async def create_google_user(
        self,
        google_id: str,
        email: str,
        name: str | None = None,
        picture: str | None = None,
    ) -> tuple[User, UserCredential]:
        """Create a new User and a linked Google OAuth credential."""
        user = User(email=email, name=name, picture=picture, email_verified=True)
        self.db.add(user)
        await self.db.flush()

        credential = UserCredential(
            user_id=user.id,
            provider=AuthProvider.GOOGLE,
            provider_user_id=google_id,
        )
        self.db.add(credential)
        await self.db.flush()
        await self.db.refresh(user)
        await self.db.refresh(credential)
        return user, credential

    async def create_email_user(
        self,
        email: str,
        password_hash: str,
        name: str | None = None,
    ) -> tuple[User, UserCredential]:
        """Create a new User and a linked email/password credential."""
        user = User(email=email, name=name, email_verified=False)
        self.db.add(user)
        await self.db.flush()

        credential = UserCredential(
            user_id=user.id,
            provider=AuthProvider.EMAIL,
            provider_user_id=email,
            password_hash=password_hash,
        )
        self.db.add(credential)
        await self.db.flush()
        await self.db.refresh(user)
        await self.db.refresh(credential)
        return user, credential

    # ------------------------------------------------------------------
    # Profile updates
    # ------------------------------------------------------------------

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
