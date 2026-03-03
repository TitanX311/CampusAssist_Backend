from pydantic import BaseModel, Field


class GoogleAuthRequest(BaseModel):
    """
    The Android client authenticates with Google via the Google Sign-In SDK or
    Credential Manager and receives a Google ID token. Forward that token here.
    The server verifies it with Google and issues a session access + refresh token.
    """

    id_token: str = Field(
        description="Google ID token obtained from Google Sign-In on the Android client"
    )


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    picture: str | None


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
