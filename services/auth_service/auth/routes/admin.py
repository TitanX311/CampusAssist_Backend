"""
Admin-only management routes — gated by require_super_admin dependency.

All role checks are live DB lookups (no JWT claim trusted).

Bootstrap: the very first SUPER_ADMIN must be set directly in the DB:
  kubectl exec -it deployment/postgres -n dev -- \
    psql -U <user> -d <db> -c \
    "UPDATE users SET type='SUPER_ADMIN' WHERE email='you@example.com';"
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from auth.config.database import get_db
from auth.dependencies.auth import TokenPayload, require_super_admin
from auth.models.user import UserType
from auth.repositories.user_repository import UserRepository

router = APIRouter(prefix="/auth/admin", tags=["Admin"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AdminUserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    picture: str | None
    type: str
    is_active: bool
    email_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AdminUserListResponse(BaseModel):
    items: list[AdminUserResponse]
    total: int
    page: int
    page_size: int


class UpdateTypeRequest(BaseModel):
    type: UserType


class UpdateActiveRequest(BaseModel):
    is_active: bool


class UpdateProfileRequest(BaseModel):
    name: str | None = None
    picture: str | None = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get(
    "/users/{user_id}",
    response_model=AdminUserResponse,
    summary="[Admin] Get a user by ID",
)
async def get_user(
    user_id: str,
    _admin: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return AdminUserResponse.model_validate(user)


@router.get(
    "/users",
    response_model=AdminUserListResponse,
    summary="[Admin] List all users",
    description=(
        "Paginated user list with optional filters.\n\n"
        "- `search` — case-insensitive substring match on email **or** name.\n"
        "- `user_type` — exact match: `USER`, `COLLEGE`, or `SUPER_ADMIN`.\n"
        "- `is_active` — `true` or `false`."
    ),
)
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, description="Filter by email or name"),
    user_type: str | None = Query(default=None, description="Filter by type: USER | COLLEGE | SUPER_ADMIN"),
    is_active: bool | None = Query(default=None, description="Filter by active status"),
    _admin: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserListResponse:
    repo = UserRepository(db)
    if search or user_type is not None or is_active is not None:
        users, total = await repo.search_all(
            search=search, user_type=user_type, is_active=is_active,
            page=page, page_size=page_size,
        )
    else:
        users, total = await repo.get_all(page=page, page_size=page_size)
    return AdminUserListResponse(
        items=[AdminUserResponse.model_validate(u) for u in users],
        total=total, page=page, page_size=page_size,
    )


@router.patch(
    "/users/{user_id}/profile",
    response_model=AdminUserResponse,
    summary="[Admin] Update user profile (name, picture)",
    description="Overwrite a user's display name and/or profile picture URL. Requires SUPER_ADMIN role.",
)
async def update_user_profile(
    user_id: str,
    body: UpdateProfileRequest,
    _admin: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user = await repo.update_profile(user, name=body.name, picture=body.picture)
    return AdminUserResponse.model_validate(user)


@router.patch(
    "/users/{user_id}/type",
    response_model=AdminUserResponse,
    summary="[Admin] Change a user's type",
    description=(
        "Promote or demote a user.\n\n"
        "Valid values: `USER`, `COLLEGE`, `SUPER_ADMIN`.\n\n"
        "To bootstrap the first super admin, set the type directly in the DB — "
        "no admin exists yet so this endpoint cannot be used for the first promotion."
    ),
)
async def update_user_type(
    user_id: str,
    body: UpdateTypeRequest,
    _admin: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user = await repo.update_type(user, body.type)
    return AdminUserResponse.model_validate(user)


@router.patch(
    "/users/{user_id}/active",
    response_model=AdminUserResponse,
    summary="[Admin] Activate or deactivate a user account",
)
async def update_user_active(
    user_id: str,
    body: UpdateActiveRequest,
    _admin: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user = await repo.update_active(user, body.is_active)
    return AdminUserResponse.model_validate(user)
