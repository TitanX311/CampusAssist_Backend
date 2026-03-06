"""
require_community_college_admin dependency — verifies that the calling user is
either a SUPER_ADMIN or an admin of the parent college of a given community.

The college admin list is always fetched live from college_service via gRPC,
so no JWT claim is trusted for this authorisation decision.
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from community.config.database import get_db
from community.config.settings import get_settings
from community.dependencies.auth import TokenPayload, get_current_user
from community.grpc import auth_client, college_client
from community.repositories.community_repository import CommunityRepository


async def require_community_college_admin(
    community_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TokenPayload:
    """Raises 403 unless the caller is a SUPER_ADMIN or an admin of the
    community's parent college (verified live via gRPC)."""
    settings = get_settings()

    # SUPER_ADMIN always bypasses college-level checks
    user_type = await auth_client.get_user_type(
        settings.AUTH_GRPC_TARGET, current_user.user_id
    )
    if user_type == "SUPER_ADMIN":
        return current_user

    # Fetch the community to get parent_colleges
    repo = CommunityRepository(db)
    community = await repo.get_by_id(community_id)
    if community is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found.",
        )

    if not community.parent_colleges:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This community has no associated college. Only SUPER_ADMIN can manage it.",
        )

    # Check if the caller is an admin of any parent college
    for college_id in community.parent_colleges:
        resp = await college_client.get_college(
            settings.COLLEGE_GRPC_TARGET, str(college_id)
        )
        if resp and resp.found and current_user.user_id in resp.admin_users:
            return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You must be a college admin to perform this action.",
    )
