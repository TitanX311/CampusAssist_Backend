"""JWT-based authentication dependency for feed_service.

Validates Bearer tokens using the shared SECRET_KEY so feed_service can
authenticate requests without an extra gRPC hop to auth_service.
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from feed.config.settings import get_settings

_bearer = HTTPBearer(auto_error=True)


@dataclass
class TokenPayload:
    user_id: str
    user_type: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> TokenPayload:
    settings = get_settings()
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenPayload(user_id=user_id, user_type=payload.get("type", "USER"))
