"""Admin panel — user management.
Proxies to auth_service admin routes.

GET    /admin/users                        — list all users (paginated, filterable)
GET    /admin/users/{id}                   — get a user by ID
PATCH  /admin/users/{id}/type             — change user type
PATCH  /admin/users/{id}/active           — activate / deactivate account
PATCH  /admin/users/{id}/profile          — update name / picture
"""
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from admin.config.settings import Settings, get_settings
from admin.dependencies.auth import TokenPayload, require_super_admin
from admin.http.client import api_get, api_patch, raise_for_upstream

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])


class UpdateTypeBody(BaseModel):
    type: str  # "USER" | "COLLEGE" | "SUPER_ADMIN"


class UpdateActiveBody(BaseModel):
    is_active: bool


class UpdateProfileBody(BaseModel):
    name: str | None = None
    picture: str | None = None


@router.get(
    "",
    summary="[Admin] List all users",
    description=(
        "Paginated user list.\n\n"
        "Filters: `search` (email or name), `user_type`, `is_active`. "
        "Requires SUPER_ADMIN role."
    ),
)
async def list_users(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, description="Filter by email or name"),
    user_type: str | None = Query(default=None, description="USER | COLLEGE | SUPER_ADMIN"),
    is_active: bool | None = Query(default=None, description="Filter by active status"),
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    params: dict = {"page": page, "page_size": page_size}
    if search is not None:
        params["search"] = search
    if user_type is not None:
        params["user_type"] = user_type
    if is_active is not None:
        params["is_active"] = str(is_active).lower()
    resp = await api_get(
        f"{settings.AUTH_SERVICE_URL}/api/auth/admin/users",
        request,
        params,
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


@router.get(
    "/{user_id}",
    summary="[Admin] Get a user by ID",
    description="Returns a single user record. Requires SUPER_ADMIN role.",
)
async def get_user(
    user_id: str,
    request: Request,
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_get(
        f"{settings.AUTH_SERVICE_URL}/api/auth/admin/users/{user_id}",
        request,
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


@router.patch(
    "/{user_id}/type",
    summary="[Admin] Change a user's type",
    description=(
        "Promote or demote a user. Valid types: `USER`, `COLLEGE`, `SUPER_ADMIN`. "
        "Requires SUPER_ADMIN role."
    ),
)
async def update_user_type(
    user_id: str,
    body: UpdateTypeBody,
    request: Request,
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_patch(
        f"{settings.AUTH_SERVICE_URL}/api/auth/admin/users/{user_id}/type",
        request,
        body.model_dump(),
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


@router.patch(
    "/{user_id}/active",
    summary="[Admin] Activate or deactivate a user account",
    description="Set `is_active` to `true` or `false`. Requires SUPER_ADMIN role.",
)
async def update_user_active(
    user_id: str,
    body: UpdateActiveBody,
    request: Request,
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_patch(
        f"{settings.AUTH_SERVICE_URL}/api/auth/admin/users/{user_id}/active",
        request,
        body.model_dump(),
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


@router.patch(
    "/{user_id}/profile",
    summary="[Admin] Update user name / picture",
    description="Overwrite display name and/or profile picture URL. Requires SUPER_ADMIN role.",
)
async def update_user_profile(
    user_id: str,
    body: UpdateProfileBody,
    request: Request,
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_patch(
        f"{settings.AUTH_SERVICE_URL}/api/auth/admin/users/{user_id}/profile",
        request,
        body.model_dump(exclude_none=True),
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)
