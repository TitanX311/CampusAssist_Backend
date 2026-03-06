"""
JWT authentication dependency for post_service.

The access token is issued and signed by auth_service using HS256 + SECRET_KEY.
Post service shares the same secret so it can verify tokens locally —
no network call to auth_service required on every request.

Usage in a route:

    from post.dependencies.auth import get_current_user, TokenPayload

    @router.get("/example")
    async def example(current_user: TokenPayload = Depends(get_current_user)):
        return {"user_id": current_user.user_id}
"""

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from post.config.settings import get_settings

settings = get_settings()

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class TokenPayload:
    """Decoded, validated claims extracted from an access token."""

    user_id: str


def _decode(token: str) -> TokenPayload:
    """Decode and validate a JWT access token. Raises HTTP 401 on any failure."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenPayload(user_id=user_id)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> TokenPayload:
    """
    FastAPI dependency — require a valid Bearer token.
    Raises HTTP 401 if the token is missing, expired, or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _decode(credentials.credentials)
