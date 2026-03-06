"""
JWT authentication + live super-admin role check for admin_service.

TokenPayload contains only user_id (no role claims — roles are always
fetched live from auth_service via gRPC so revocations are instant).
"""
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from admin.config.settings import get_settings
from admin.grpc import auth_client

_bearer = HTTPBearer(auto_error=True)


@dataclass(frozen=True)
class TokenPayload:
    user_id: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> TokenPayload:
    """Decode and validate the JWT. Raises 401 on any failure."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )
    return TokenPayload(user_id=str(user_id))


async def require_super_admin(
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """Raise 403 unless the caller's live DB user_type is SUPER_ADMIN."""
    settings = get_settings()
    user_type = await auth_client.get_user_type(
        settings.AUTH_GRPC_TARGET, current_user.user_id
    )
    if user_type != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required.",
        )
    return current_user
