from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.config.database import get_db
from auth.schemas.auth import (
    EmailLoginRequest,
    EmailRegisterRequest,
    GoogleAuthRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    ResendVerificationRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from auth.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

_TOKEN_RESPONSE_EXAMPLE = {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 900,
    "user": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "name": "Jane Doe",
        "picture": "https://lh3.googleusercontent.com/...",
        "email_verified": True,
        "type": "google",
    },
}

_ERROR_401 = {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "Invalid or expired credentials."}}}}
_ERROR_409 = {"description": "Conflict", "content": {"application/json": {"example": {"detail": "An account with this email already exists."}}}}
_ERROR_422 = {"description": "Validation Error", "content": {"application/json": {"example": {"detail": [{"loc": ["body", "email"], "msg": "value is not a valid email address", "type": "value_error.email"}]}}}}


@router.post(
    "/google",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Sign in / sign up with Google",
    description=(
        "Verify a Google ID token obtained from the Android **Google Sign-In SDK** "
        "or **Credential Manager** and exchange it for a campus-assist session.\n\n"
        "**Flow:**\n"
        "1. Client authenticates with Google and receives a Google ID token.\n"
        "2. Client sends that token to this endpoint.\n"
        "3. Server verifies the token against Google's public keys.\n"
        "4. If the email is new a user record is created automatically; "
        "otherwise the existing record is updated (name, picture).\n"
        "5. Returns an `access_token` (short-lived) and `refresh_token` (long-lived).\n\n"
        "**Token usage:**\n"
        "- Include `access_token` in the `Authorization: Bearer <token>` header on "
        "every subsequent API call.\n"
        "- When the access token expires (401), call `POST /api/auth/refresh` with the "
        "`refresh_token` to obtain a new pair.\n\n"
        "**`email_verified`** will be `true` for Google accounts because Google "
        "guarantees the email is owned by the user."
    ),
    responses={
        200: {
            "description": "Authenticated successfully",
            "content": {"application/json": {"example": _TOKEN_RESPONSE_EXAMPLE}},
        },
        401: {"description": "Invalid or expired Google ID token", "content": {"application/json": {"example": {"detail": "Google token verification failed."}}}},
        422: _ERROR_422,
    },
)
async def google_auth(data: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).google_auth(data)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account with email & password",
    description=(
        "Create a new email/password account.\n\n"
        "**Rules:**\n"
        "- `email` must be a valid, unique email address.\n"
        "- `password` must be at least 8 characters (stored as a bcrypt hash; "
        "only the first 72 bytes are significant).\n"
        "- `name` is optional.\n\n"
        "On success, returns the same `TokenResponse` as login so the user is "
        "immediately signed in. `email_verified` starts as `false`."
    ),
    responses={
        201: {
            "description": "Account created and signed in",
            "content": {"application/json": {"example": {**_TOKEN_RESPONSE_EXAMPLE, "user": {**_TOKEN_RESPONSE_EXAMPLE["user"], "email_verified": False, "type": "email"}}}}},
        409: _ERROR_409,
        422: _ERROR_422,
    },
)
async def register_email(
    data: EmailRegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService(db).register_email(data, background_tasks=background_tasks)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Sign in with email & password",
    description=(
        "Authenticate an existing email/password account.\n\n"
        "Returns an `access_token` + `refresh_token` on success.\n\n"
        "**Common errors:**\n"
        "- `401` — email not found, wrong password, or the account was created via "
        "Google (no password set)."
    ),
    responses={
        200: {
            "description": "Signed in successfully",
            "content": {"application/json": {"example": _TOKEN_RESPONSE_EXAMPLE}},
        },
        401: _ERROR_401,
        422: _ERROR_422,
    },
)
async def login_email(data: EmailLoginRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).login_email(data)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh tokens",
    description=(
        "Exchange a valid **refresh token** for a new `access_token` + `refresh_token` "
        "pair (token rotation).\n\n"
        "**When to call:** whenever an API request returns `401 Unauthorized` because "
        "the access token has expired.\n\n"
        "**Important:** each refresh token is single-use — the old one is invalidated "
        "on every call. Store the new refresh token returned in the response."
    ),
    responses={
        200: {
            "description": "New token pair issued",
            "content": {"application/json": {"example": _TOKEN_RESPONSE_EXAMPLE}},
        },
        401: {"description": "Refresh token is invalid, expired, or already used", "content": {"application/json": {"example": {"detail": "Invalid or expired refresh token."}}}},
        422: _ERROR_422,
    },
)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).refresh(data)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout (revoke refresh token)",
    description=(
        "Revoke a refresh token so it can no longer be used to obtain new access "
        "tokens. The client should discard both tokens after calling this endpoint.\n\n"
        "**Note:** access tokens are stateless JWTs and cannot be individually revoked. "
        "They expire naturally after their `expires_in` window."
    ),
    responses={
        204: {"description": "Token revoked — no content returned"},
        422: _ERROR_422,
    },
)
async def logout(data: LogoutRequest, db: AsyncSession = Depends(get_db)):
    await AuthService(db).logout(data.refresh_token)


@router.post(
    "/email/verify",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify email address",
    description=(
        "Consume a single-use verification token from the link emailed after "
        "registration.\n\n"
        "**Flow:**\n"
        "1. User registers → server sends a verification email with a link "
        "containing `?token=<token>`.\n"
        "2. Client extracts `token` from the URL and calls this endpoint.\n"
        "3. On success the account's `email_verified` flag is set to `true`.\n\n"
        "**After verification** the client should call `POST /api/auth/refresh` to "
        "receive a fresh token pair with `email_verified: true` in the response."
    ),
    responses={
        200: {"description": "Email verified (or already verified)"},
        400: {
            "description": "Token invalid, expired, or already used",
            "content": {"application/json": {"example": {"detail": "Invalid or expired verification token"}}},
        },
        422: _ERROR_422,
    },
)
async def verify_email(
    data: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService(db).verify_email(data)


@router.post(
    "/email/resend",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Re-send verification email",
    description=(
        "Request a new email-verification link.\n\n"
        "Always returns `200 OK` to prevent email enumeration — even if the address "
        "is unknown or already verified, the response message is identical.\n\n"
        "A resend invalidates any previous (unused) verification token for that "
        "account so only the latest link works."
    ),
    responses={
        200: {"description": "Response sent (or silently skipped)"},
        422: _ERROR_422,
    },
)
async def resend_verification(
    data: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService(db).resend_verification(data, background_tasks=background_tasks)
