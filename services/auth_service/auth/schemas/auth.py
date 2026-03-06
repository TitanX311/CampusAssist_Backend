from pydantic import BaseModel, EmailStr, Field


class GoogleAuthRequest(BaseModel):
    """
    The Android client authenticates with Google via the Google Sign-In SDK or
    Credential Manager and receives a Google ID token. Forward that token here.
    The server verifies it with Google and issues a session access + refresh token.
    """

    id_token: str = Field(
        description="Google ID token obtained from Google Sign-In on the Android client"
    )


class EmailRegisterRequest(BaseModel):
    """Register a new account using an email address and password."""

    email: EmailStr
    password: str = Field(min_length=8, description="Minimum 8 characters")
    name: str | None = Field(default=None, description="Optional display name")


class EmailLoginRequest(BaseModel):
    """Sign in with an existing email/password account."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    picture: str | None
    email_verified: bool
    type: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token lifetime in seconds")
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    """Token extracted from the verification link."""

    token: str


class ResendVerificationRequest(BaseModel):
    """Request a fresh verification email for the given address."""

    email: EmailStr


class MessageResponse(BaseModel):
    """Generic single-message response."""

    message: str
