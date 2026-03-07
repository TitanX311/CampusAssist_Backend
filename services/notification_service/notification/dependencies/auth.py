"""
JWT authentication dependency for notification_service.

Tokens are issued and signed by auth_service with HS256 + SECRET_KEY.
Notification service shares the same secret so it can verify tokens
locally — no network call to auth_service required.
"""

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from notification.config.settings import get_settings

settings = get_settings()

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class TokenPayload:
    user_id: str
    user_type: str


def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT. Raises HTTP 401 on any failure.

    Exposed as a plain function (not just a dependency) so the WebSocket
    endpoint can call it directly with the token from the query string.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing subject claim.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_type: str = payload.get("user_type", "USER")
    return TokenPayload(user_id=user_id, user_type=user_type)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> TokenPayload:
    """FastAPI dependency — validates the Bearer token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)
