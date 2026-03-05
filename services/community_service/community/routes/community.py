from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from community.config.database import get_db
from community.dependencies.auth import TokenPayload, get_current_user
from community.repositories.community_repository import CommunityRepository
from community.schemas.community import CommunityListResponse, CommunityResponse

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
