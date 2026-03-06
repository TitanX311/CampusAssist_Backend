import logging
from datetime import datetime, timezone

import bcrypt as _bcrypt
from fastapi import BackgroundTasks, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from auth.config.settings import get_settings
from auth.repositories.email_verification_repository import EmailVerificationRepository
from auth.repositories.refresh_token_repository import RefreshTokenRepository
from auth.repositories.user_repository import UserRepository
from auth.schemas.auth import (
    EmailLoginRequest,
    EmailRegisterRequest,
    GoogleAuthRequest,
    MessageResponse,
    RefreshRequest,
    ResendVerificationRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)
from auth.services import email_service
from auth.services.token_service import TokenService

settings = get_settings()

# Use bcrypt directly — passlib 1.7.4 is incompatible with bcrypt 4.x+ because
# passlib's internal detect_wrap_bug() passes a >72-byte test secret to bcrypt,
# which now raises ValueError instead of silently truncating.
_MAX_PW_BYTES = 72


def _hash_password(password: str) -> str:
    """Hash a password with bcrypt, truncating to 72 bytes first."""
    pw_bytes = password.encode("utf-8")[:_MAX_PW_BYTES]
    return _bcrypt.hashpw(pw_bytes, _bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    """Verify a bcrypt hash, truncating the candidate to 72 bytes first."""
    pw_bytes = password.encode("utf-8")[:_MAX_PW_BYTES]
    return _bcrypt.checkpw(pw_bytes, hashed.encode("utf-8"))


def _is_expired(dt: datetime) -> bool:
    now = datetime.now(timezone.utc)
    aware_dt = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return now > aware_dt


def _user_response(user) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        picture=user.picture,
        email_verified=user.email_verified,
        type=user.type.value,
    )


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)
        self.email_verif = EmailVerificationRepository(db)

    # ------------------------------------------------------------------
    # Google OAuth
    # ------------------------------------------------------------------

    async def google_auth(self, data: GoogleAuthRequest) -> TokenResponse:
        # Verify the Google ID token signature and claims
        try:
            id_info = google_id_token.verify_oauth2_token(
                data.id_token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google ID token: {exc}",
            )

        google_id: str = id_info["sub"]
        email: str = id_info.get("email", "")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account has no verified email address",
            )
        name: str | None = id_info.get("name")
        picture: str | None = id_info.get("picture")

        # Try to find the existing Google credential row
        credential = await self.users.get_credential_by_google_id(google_id)

        if credential is None:
            # First-time Google sign-in: make sure no email/password account
            # already owns this email address.
            existing = await self.users.get_by_email(email)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already associated with a different account",
                )
            user, _ = await self.users.create_google_user(
                google_id=google_id,
                email=email,
                name=name,
                picture=picture,
            )
        else:
            # Refresh display name and avatar on every subsequent login
            user = await self.users.get_by_id(credential.user_id)
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Credential exists but user record is missing",
                )
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
            user=_user_response(user),
        )

    # ------------------------------------------------------------------
    # Email / password — register
    # ------------------------------------------------------------------

    async def register_email(
        self,
        data: EmailRegisterRequest,
        background_tasks: BackgroundTasks | None = None,
    ) -> TokenResponse:
        existing = await self.users.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with that email already exists",
            )

        if settings.DEBUG:
            logger.debug("[DEBUG] register_email — email: %s | password: %s", data.email, data.password)

        password_hash = _hash_password(data.password)
        user, _ = await self.users.create_email_user(
            email=data.email,
            password_hash=password_hash,
            name=data.name,
        )

        # Create a verification token and dispatch the email asynchronously.
        ev_token = await self.email_verif.create(user.id)
        if background_tasks is not None:
            background_tasks.add_task(
                email_service.send_verification_email, user.email, ev_token.token
            )
        else:
            await email_service.send_verification_email(user.email, ev_token.token)

        access_token, expires_in = TokenService.create_access_token(user.id)
        refresh_token = await self.refresh_tokens.create(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token.token,
            expires_in=expires_in,
            user=_user_response(user),
        )

    # ------------------------------------------------------------------
    # Email / password — login
    # ------------------------------------------------------------------

    async def login_email(self, data: EmailLoginRequest) -> TokenResponse:
        credential = await self.users.get_credential_by_email_provider(data.email)

        if settings.DEBUG:
            logger.debug("[DEBUG] login_email — email: %s | password: %s", data.email, data.password)

        if credential is None or not credential.password_hash or not _verify_password(
            data.password, credential.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        user = await self.users.get_by_id(credential.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Credential exists but user record is missing",
            )

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
            user=_user_response(user),
        )

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

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
            user=_user_response(user),
        )

    async def logout(self, refresh_token: str) -> None:
        token_record = await self.refresh_tokens.get_by_token(refresh_token)
        if token_record and not token_record.revoked:
            await self.refresh_tokens.revoke(token_record)

    # ------------------------------------------------------------------
    # Email verification
    # ------------------------------------------------------------------

    async def verify_email(self, data: VerifyEmailRequest) -> MessageResponse:
        record = await self.email_verif.get_by_token(data.token)

        if record is None or _is_expired(record.expires_at):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token",
            )
        if record.used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has already been used",
            )

        user = await self.users.get_by_id(record.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User associated with this token no longer exists",
            )

        if user.email_verified:
            return MessageResponse(message="Email is already verified")

        await self.email_verif.mark_used(record)
        await self.users.mark_email_verified(user)
        return MessageResponse(message="Email verified successfully")

    async def resend_verification(
        self,
        data: ResendVerificationRequest,
        background_tasks: BackgroundTasks | None = None,
    ) -> MessageResponse:
        # Always return 200 to prevent email enumeration.
        _generic = MessageResponse(
            message=(
                "If an unverified account exists for that address, "
                "a new verification link has been sent."
            )
        )

        user = await self.users.get_by_email(data.email)
        if user is None or user.email_verified:
            return _generic

        ev_token = await self.email_verif.create(user.id)
        if background_tasks is not None:
            background_tasks.add_task(
                email_service.send_verification_email, user.email, ev_token.token
            )
        else:
            await email_service.send_verification_email(user.email, ev_token.token)

        return _generic
