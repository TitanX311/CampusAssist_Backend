"""
Admin-only community management routes — gated by require_super_admin.

GET  /community/admin/list          — list ALL communities (no membership filter)
DELETE /community/admin/{id}        — force-delete any community
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from community.config.database import get_db
from community.dependencies.admin import require_super_admin
from community.dependencies.auth import TokenPayload
from community.repositories.community_repository import CommunityRepository
from community.schemas.community import CommunityListResponse, CommunityResponse

admin_router = APIRouter(prefix="/community/admin", tags=["Community Admin"])


@admin_router.get(
    "/list",
    response_model=CommunityListResponse,
    summary="[Admin] List all communities",
    description="Returns every community regardless of membership. Requires SUPER_ADMIN role.",
)
async def list_all_communities(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> CommunityListResponse:
    repo = CommunityRepository(db)
    items, total = await repo.get_all(page=page, page_size=page_size)
    return CommunityListResponse(
        items=[CommunityResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@admin_router.delete(
    "/{community_id}",
    status_code=status.HTTP_200_OK,
    summary="[Admin] Force-delete a community",
    description="Permanently deletes any community regardless of who owns it. Requires SUPER_ADMIN role.",
)
async def admin_delete_community(
    community_id: str,
    _: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = CommunityRepository(db)
    community = await repo.get_by_id(community_id)
    if community is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found.",
        )
    await repo.delete(community)
    return {"community_id": community_id, "message": "Community deleted."}
