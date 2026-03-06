"""
require_super_admin dependency — calls auth_service via gRPC to verify
the calling user's type is SUPER_ADMIN in the live DB.

No JWT claim is trusted for this check; the role is always fetched fresh.
"""
from fastapi import Depends, HTTPException, status

from attachment.config.settings import get_settings
from attachment.dependencies.auth import TokenPayload, get_current_user
from attachment.grpc import auth_client


async def require_super_admin(
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """Raises 403 unless the user's live DB type is SUPER_ADMIN."""
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
