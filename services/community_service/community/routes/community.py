import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from community.config.database import get_db
from community.dependencies.auth import TokenPayload, get_current_user
from community.models.community import CommunityType
from community.repositories.community_repository import CommunityRepository
from community.schemas.community import (
    CommunityListResponse,
    CommunityResponse,
    JoinCommunityResponse,
)

router = APIRouter(prefix="/community", tags=["Community"])


@router.get(
    "/my-communities",
    response_model=CommunityListResponse,
    summary="Get communities I'm a member of",
    description=(
        "Returns a paginated list of all communities where the authenticated user "
        "is an active member. Requires a valid Bearer access token."
    ),
)
async def get_my_communities(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommunityListResponse:
    repo = CommunityRepository(db)
    items, total = await repo.get_by_member(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )
    return CommunityListResponse(
        items=[CommunityResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/{community_id}/join",
    response_model=JoinCommunityResponse,
    status_code=status.HTTP_200_OK,
    summary="Join or request to join a community",
    description=(
        "PUBLIC communities: user is added as a member immediately.\n\n"
        "PRIVATE communities: user is added to the pending requests list. "
        "A moderator must accept the request before the user becomes a member."
    ),
)
async def join_community(
    community_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JoinCommunityResponse:
    repo = CommunityRepository(db)

    community = await repo.get_by_id(community_id)
    if community is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found.",
        )

    user_id = current_user.user_id
    uid = uuid.UUID(user_id)

    # Already a member?
    if uid in community.member_users:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already a member of this community.",
        )

    if community.type == CommunityType.PUBLIC:
        await repo.add_member(community, user_id)
        return JoinCommunityResponse(
            community_id=community_id,
            status="joined",
            message="You have joined the community.",
        )

    # PRIVATE — check if request already pending
    if uid in community.requested_users:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending join request for this community.",
        )

    await repo.request_join(community, user_id)
    return JoinCommunityResponse(
        community_id=community_id,
        status="requested",
        message="Your join request has been sent. You will be added once a moderator approves it.",
    )
