import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from college.config.database import get_db
from college.config.settings import get_settings
from college.dependencies.admin import require_college_type
from college.dependencies.auth import TokenPayload, get_current_user
from college.grpc import auth_client
from college.repositories.college_repository import CollegeRepository
from college.schemas.college import (
    AddCommunityResponse,
    AdminActionResponse,
    CollegeListResponse,
    CollegeResponse,
    CollegeUserListResponse,
    CreateCollegeRequest,
    DeleteCollegeResponse,
    RemoveCommunityResponse,
    UpdateCollegeRequest,
)

router = APIRouter(prefix="/college", tags=["College"])
_bearer = HTTPBearer(auto_error=False)

_EXAMPLE = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "MIT",
    "contact_email": "admin@mit.edu",
    "physical_address": "77 Massachusetts Ave, Cambridge, MA",
    "admin_users": [],
    "communities": [],
    "created_at": "2026-03-01T10:00:00+00:00",
    "updated_at": "2026-03-01T10:00:00+00:00",
}
_401 = {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "Not authenticated."}}}}
_403 = {"description": "Forbidden", "content": {"application/json": {"example": {"detail": "Only a college admin can perform this action."}}}}
_404 = {"description": "Not Found", "content": {"application/json": {"example": {"detail": "College not found."}}}}


def _assert_admin(college, current_user: TokenPayload) -> None:
    uid = uuid.UUID(current_user.user_id)
    if uid not in (college.admin_users or []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only a college admin can perform this action.")


# ---------------------------------------------------------------------------
# GET /college  — list all colleges
# ---------------------------------------------------------------------------

@router.get("", response_model=CollegeListResponse, summary="List all colleges")
async def list_colleges(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CollegeListResponse:
    repo = CollegeRepository(db)
    items, total = await repo.get_all(page=page, page_size=page_size)
    return CollegeListResponse(
        items=[CollegeResponse.model_validate(c) for c in items],
        total=total, page=page, page_size=page_size,
    )


# ---------------------------------------------------------------------------
# POST /college  — create a college (COLLEGE-type users only)
# ---------------------------------------------------------------------------

@router.post(
    "", response_model=CollegeResponse, status_code=status.HTTP_201_CREATED,
    summary="Create a college",
    description="Only users with `type=COLLEGE` (or `SUPER_ADMIN`) may create a college. The creator is automatically added to `admin_users`.",
    responses={201: {"content": {"application/json": {"example": _EXAMPLE}}}, 401: _401, 403: _403},
)
async def create_college(
    body: CreateCollegeRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CollegeResponse:
    _settings = get_settings()
    user_type = await auth_client.get_user_type(_settings.AUTH_GRPC_TARGET, current_user.user_id)
    if user_type not in ("COLLEGE", "SUPER_ADMIN"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only users of type COLLEGE can create a college.")

    repo = CollegeRepository(db)
    if await repo.get_by_name(body.name):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A college with this name already exists.")

    # Ensure the creator is always an admin
    admin_set = {uuid.UUID(current_user.user_id)} | set(body.admin_users)
    college = await repo.create(
        name=body.name,
        contact_email=str(body.contact_email),
        physical_address=body.physical_address,
        admin_users=list(admin_set),
    )
    return CollegeResponse.model_validate(college)


# ---------------------------------------------------------------------------
# GET /college/my  — list colleges managed by the current user (COLLEGE type)
# ---------------------------------------------------------------------------

@router.get(
    "/my",
    response_model=CollegeListResponse,
    summary="List my managed colleges",
    description=(
        "Returns all colleges where the authenticated user is listed in "
        "`admin_users`.\n\n"
        "**Only COLLEGE-type users (or SUPER_ADMIN) can call this endpoint.**"
    ),
    responses={401: _401, 403: _403},
)
async def list_my_colleges(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: TokenPayload = Depends(require_college_type),
    db: AsyncSession = Depends(get_db),
) -> CollegeListResponse:
    repo = CollegeRepository(db)
    items, total = await repo.get_by_admin(
        current_user.user_id, page=page, page_size=page_size
    )
    return CollegeListResponse(
        items=[CollegeResponse.model_validate(c) for c in items],
        total=total, page=page, page_size=page_size,
    )


# ---------------------------------------------------------------------------
# GET /college/{college_id}
# ---------------------------------------------------------------------------

@router.get("/{college_id}", response_model=CollegeResponse, summary="Get a college by ID",
    responses={200: {"content": {"application/json": {"example": _EXAMPLE}}}, 401: _401, 404: _404})
async def get_college(
    college_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CollegeResponse:
    repo = CollegeRepository(db)
    college = await repo.get_by_id(college_id)
    if college is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="College not found.")
    return CollegeResponse.model_validate(college)


# ---------------------------------------------------------------------------
# PATCH /college/{college_id}
# ---------------------------------------------------------------------------

@router.patch("/{college_id}", response_model=CollegeResponse, summary="Update a college",
    responses={200: {"content": {"application/json": {"example": _EXAMPLE}}}, 401: _401, 403: _403, 404: _404})
async def update_college(
    college_id: str,
    body: UpdateCollegeRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CollegeResponse:
    repo = CollegeRepository(db)
    college = await repo.get_by_id(college_id)
    if college is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="College not found.")
    _assert_admin(college, current_user)
    college = await repo.update(
        college,
        name=body.name,
        contact_email=str(body.contact_email) if body.contact_email else None,
        physical_address=body.physical_address,
        admin_users=body.admin_users,
    )
    return CollegeResponse.model_validate(college)


# ---------------------------------------------------------------------------
# DELETE /college/{college_id}
# ---------------------------------------------------------------------------

@router.delete("/{college_id}", response_model=DeleteCollegeResponse, summary="Delete a college",
    responses={401: _401, 403: _403, 404: _404})
async def delete_college(
    college_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeleteCollegeResponse:
    repo = CollegeRepository(db)
    college = await repo.get_by_id(college_id)
    if college is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="College not found.")
    _assert_admin(college, current_user)
    await repo.delete(college)
    return DeleteCollegeResponse(college_id=college_id, message="College deleted successfully.")


# ---------------------------------------------------------------------------
# POST /college/{college_id}/communities/{community_id}  — link a community
# ---------------------------------------------------------------------------

@router.post("/{college_id}/communities/{community_id}", response_model=AddCommunityResponse,
    summary="Add a community to a college",
    responses={401: _401, 403: _403, 404: _404})
async def add_community(
    college_id: str,
    community_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AddCommunityResponse:
    repo = CollegeRepository(db)
    college = await repo.get_by_id(college_id)
    if college is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="College not found.")
    _assert_admin(college, current_user)
    await repo.add_community(college, community_id)
    return AddCommunityResponse(college_id=college_id, community_id=community_id, message="Community linked to college.")


# ---------------------------------------------------------------------------
# DELETE /college/{college_id}/communities/{community_id}  — unlink
# ---------------------------------------------------------------------------

@router.delete("/{college_id}/communities/{community_id}", response_model=RemoveCommunityResponse,
    summary="Remove a community from a college",
    responses={401: _401, 403: _403, 404: _404})
async def remove_community(
    college_id: str,
    community_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RemoveCommunityResponse:
    repo = CollegeRepository(db)
    college = await repo.get_by_id(college_id)
    if college is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="College not found.")
    _assert_admin(college, current_user)
    await repo.remove_community(college, community_id)
    return RemoveCommunityResponse(college_id=college_id, community_id=community_id, message="Community unlinked from college.")


# ---------------------------------------------------------------------------
# GET /college/{college_id}/users  — list all users across all communities
# ---------------------------------------------------------------------------

@router.get("/{college_id}/users", response_model=CollegeUserListResponse,
    summary="List all users in a college",
    description="Returns every user who has joined at least one community belonging to this college.",
    responses={401: _401, 404: _404})
async def list_college_users(
    college_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CollegeUserListResponse:
    from college.schemas.college import CollegeUserResponse
    repo = CollegeRepository(db)
    college = await repo.get_by_id(college_id)
    if college is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="College not found.")
    items, total = await repo.get_users(college_id, page=page, page_size=page_size)
    return CollegeUserListResponse(
        items=[CollegeUserResponse.model_validate(u) for u in items],
        total=total, page=page, page_size=page_size,
    )


# ---------------------------------------------------------------------------
# GET /college/{college_id}/communities  — list full community objects
# ---------------------------------------------------------------------------

@router.get(
    "/{college_id}/communities",
    summary="List communities for a college",
    description=(
        "Returns full community objects belonging to this college by proxying "
        "to the community service. Any authenticated user may call this."
    ),
    responses={401: _401, 404: _404},
)
async def list_college_communities(
    college_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
):
    repo = CollegeRepository(db)
    college = await repo.get_by_id(college_id)
    if college is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="College not found.")

    _settings = get_settings()
    url = f"{_settings.COMMUNITY_SERVICE_URL}/api/community/college/{college_id}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            url,
            params={"page": page, "page_size": page_size},
            headers={"Authorization": f"Bearer {credentials.credentials}"},
        )
    if resp.status_code == 200:
        return resp.json()
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


# ---------------------------------------------------------------------------
# POST /college/{college_id}/admins/{user_id}  — add an admin
# ---------------------------------------------------------------------------

@router.post(
    "/{college_id}/admins/{user_id}",
    response_model=AdminActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Add a college admin",
    description=(
        "Adds `user_id` to this college's `admin_users` list. "
        "Idempotent — calling again has no effect.\n\n"
        "**Requires:** caller must already be in `admin_users` AND have account "
        "type `COLLEGE` or `SUPER_ADMIN`."
    ),
    responses={401: _401, 403: _403, 404: _404},
)
async def add_college_admin(
    college_id: str,
    user_id: str,
    current_user: TokenPayload = Depends(require_college_type),
    db: AsyncSession = Depends(get_db),
) -> AdminActionResponse:
    repo = CollegeRepository(db)
    college = await repo.get_by_id(college_id)
    if college is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="College not found.")
    _assert_admin(college, current_user)
    await repo.add_admin(college, user_id)
    return AdminActionResponse(
        college_id=college_id,
        user_id=user_id,
        message="User added to college admins.",
    )


# ---------------------------------------------------------------------------
# DELETE /college/{college_id}/admins/{user_id}  — remove an admin
# ---------------------------------------------------------------------------

@router.delete(
    "/{college_id}/admins/{user_id}",
    response_model=AdminActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove a college admin",
    description=(
        "Removes `user_id` from this college's `admin_users` list. "
        "Idempotent — calling again has no effect.\n\n"
        "**Requires:** caller must already be in `admin_users` AND have account "
        "type `COLLEGE` or `SUPER_ADMIN`."
    ),
    responses={401: _401, 403: _403, 404: _404},
)
async def remove_college_admin(
    college_id: str,
    user_id: str,
    current_user: TokenPayload = Depends(require_college_type),
    db: AsyncSession = Depends(get_db),
) -> AdminActionResponse:
    repo = CollegeRepository(db)
    college = await repo.get_by_id(college_id)
    if college is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="College not found.")
    _assert_admin(college, current_user)
    await repo.remove_admin(college, user_id)
    return AdminActionResponse(
        college_id=college_id,
        user_id=user_id,
        message="User removed from college admins.",
    )
