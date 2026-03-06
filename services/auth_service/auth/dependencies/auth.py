"""
Auth dependency for auth_service routes.

`get_current_user` — validates the Bearer JWT and returns the user_id.
`require_super_admin` — additionally checks the DB to confirm SUPER_ADMIN type.
"""
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from auth.config.database import get_db
from auth.models.user import UserType
from auth.repositories.user_repository import UserRepository
from auth.services.token_service import TokenService

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class TokenPayload:
    user_id: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> TokenPayload:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = TokenService.verify_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenPayload(user_id=user_id)


async def require_super_admin(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TokenPayload:
    """
    FastAPI dependency — raises 403 unless the calling user's DB record
    shows type=SUPER_ADMIN.  The check is always live (no JWT claim trusted).
    """
    repo = UserRepository(db)
    user = await repo.get_by_id(current_user.user_id)
    if user is None or user.type != UserType.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required.",
        )
    return current_user
