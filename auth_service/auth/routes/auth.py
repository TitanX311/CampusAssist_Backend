from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.config.database import get_db
from auth.schemas.auth import (
    GoogleAuthRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
)
from auth.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/google",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Sign in with Google",
    description=(
        "The Android client authenticates with Google using the Google Sign-In SDK or "
        "Credential Manager and receives a Google ID token. "
        "This endpoint verifies that token with Google's public keys, then creates or "
        "updates the user record and returns a session access token + refresh token."
    ),
)
async def google_auth(data: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).google_auth(data)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate refresh token and issue new access token",
)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).refresh(data)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a refresh token (logout)",
)
async def logout(data: LogoutRequest, db: AsyncSession = Depends(get_db)):
    await AuthService(db).logout(data.refresh_token)
