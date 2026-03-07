"""
Admin-only college management routes — gated by require_super_admin.

GET    /college/admin/list      — list ALL colleges
PATCH  /college/admin/{id}      — update any college (bypasses college-admin check)
DELETE /college/admin/{id}      — force-delete any college (bypasses college-admin check)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from college.config.database import get_db
from college.dependencies.admin import require_super_admin
from college.dependencies.auth import TokenPayload
from college.repositories.college_repository import CollegeRepository
from college.schemas.college import (
    CollegeListResponse,
    CollegeResponse,
    DeleteCollegeResponse,
    UpdateCollegeRequest,
)

admin_router = APIRouter(prefix="/college/admin", tags=["College Admin"])


@admin_router.get(
    "/list",
    response_model=CollegeListResponse,
    summary="[Admin] List all colleges",
    description="Returns every college. Requires SUPER_ADMIN role.",
)
async def list_all_colleges(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> CollegeListResponse:
    repo = CollegeRepository(db)
    items, total = await repo.get_all(page=page, page_size=page_size)
    return CollegeListResponse(
        items=[CollegeResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@admin_router.patch(
    "/{college_id}",
    response_model=CollegeResponse,
    status_code=status.HTTP_200_OK,
    summary="[Admin] Update any college",
    description=(
        "Update a college's name, contact email, or physical address. "
        "Bypasses the college-admin membership check. "
        "Requires SUPER_ADMIN role."
    ),
)
async def admin_update_college(
    college_id: str,
    body: UpdateCollegeRequest,
    _: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> CollegeResponse:
    repo = CollegeRepository(db)
    college = await repo.get_by_id(college_id)
    if college is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="College not found.")
    college = await repo.update(
        college,
        name=body.name,
        contact_email=str(body.contact_email) if body.contact_email else None,
        physical_address=body.physical_address,
        admin_users=body.admin_users,
    )
    return CollegeResponse.model_validate(college)


@admin_router.delete(
    "/{college_id}",
    response_model=DeleteCollegeResponse,
    status_code=status.HTTP_200_OK,
    summary="[Admin] Force-delete any college",
    description=(
        "Permanently deletes a college regardless of who administers it. "
        "Requires SUPER_ADMIN role."
    ),
)
async def admin_delete_college(
    college_id: str,
    _: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> DeleteCollegeResponse:
    repo = CollegeRepository(db)
    college = await repo.get_by_id(college_id)
    if college is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="College not found.")
    await repo.delete(college)
    return DeleteCollegeResponse(college_id=college_id, message="College deleted by admin.")
