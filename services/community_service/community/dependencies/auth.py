"""
JWT authentication dependency for community_service.

The access token is issued and signed by auth_service using HS256 + SECRET_KEY.
Community service shares the same secret so it can verify tokens locally —
no network call to auth_service required on every request.

Usage in a route:

    from community.dependencies.auth import get_current_user, TokenPayload

    @router.get("/example")
    async def example(current_user: TokenPayload = Depends(get_current_user)):
        return {"user_id": current_user.user_id}

For optional auth (public routes that behave differently when authenticated):

    from community.dependencies.auth import get_optional_user, TokenPayload

    @router.get("/example")
    async def example(current_user: TokenPayload | None = Depends(get_optional_user)):
        ...
"""

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from community.config.settings import get_settings

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


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> TokenPayload | None:
    """
    FastAPI dependency — accept an optional Bearer token.
    Returns None if no token is present; raises HTTP 401 only if a token IS
    present but invalid.
    """
    if credentials is None:
        return None
    return _decode(credentials.credentials)
