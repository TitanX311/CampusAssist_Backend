from datetime import datetime, timezone

from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.ext.asyncio import AsyncSession

from auth.config.settings import get_settings
from auth.repositories.refresh_token_repository import RefreshTokenRepository
from auth.repositories.user_repository import UserRepository
from auth.schemas.auth import (
    GoogleAuthRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)
from auth.services.token_service import TokenService

settings = get_settings()

_google_transport = google_requests.Request()


def _is_expired(dt: datetime) -> bool:
    now = datetime.now(timezone.utc)
    aware_dt = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return now > aware_dt


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)

    async def google_auth(self, data: GoogleAuthRequest) -> TokenResponse:
        print(data)
        # Verify the Google ID token signature and claims
        try:
            id_info = google_id_token.verify_oauth2_token(
                data.id_token,
                _google_transport,
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError as exc:
            print(exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google ID token: {exc}",
            )

        google_id: str = id_info["sub"]
        email: str = id_info.get("email", "")
        name: str | None = id_info.get("name")
        picture: str | None = id_info.get("picture")

        # Upsert: find by google_id or create new user
        user = await self.users.get_by_google_id(google_id)
        if user is None:
            existing = await self.users.get_by_email(email)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already associated with a different account",
                )
            user = await self.users.create(
                google_id=google_id,
                email=email,
                name=name,
                picture=picture,
            )
        else:
            # Refresh display name and avatar on every login
            user = await self.users.update_profile(user, name=name, picture=picture)

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )

        access_token, expires_in = TokenService.create_access_token(user.id)
        refresh_token = await self.refresh_tokens.create(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token.token,
            expires_in=expires_in,
            user=UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                picture=user.picture,
            ),
        )

    async def refresh(self, data: RefreshRequest) -> TokenResponse:
        token_record = await self.refresh_tokens.get_by_token(data.refresh_token)

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        if token_record.revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )
        if _is_expired(token_record.expires_at):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
            )

        user = await self.users.get_by_id(token_record.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        # Rotate: revoke old token and issue a new pair
        await self.refresh_tokens.revoke(token_record)
        access_token, expires_in = TokenService.create_access_token(user.id)
        new_refresh_token = await self.refresh_tokens.create(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token.token,
            expires_in=expires_in,
            user=UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                picture=user.picture,
            ),
        )

    async def logout(self, refresh_token: str) -> None:
        token_record = await self.refresh_tokens.get_by_token(refresh_token)
        if token_record and not token_record.revoked:
            await self.refresh_tokens.revoke(token_record)
