"""
Admin panel — user management.
Proxies to auth_service admin routes.

GET    /admin/users                 — list all users (paginated)
GET    /admin/users/{id}            — get a user by ID
PATCH  /admin/users/{id}/type       — change user type (USER/COLLEGE/SUPER_ADMIN)
PATCH  /admin/users/{id}/active     — activate / deactivate account
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


@router.get(
    "",
    summary="[Admin] List all users",
    description="Paginated list of every registered user. Requires SUPER_ADMIN role.",
)
async def list_users(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_get(
        f"{settings.AUTH_SERVICE_URL}/api/auth/admin/users",
        request,
        {"page": page, "page_size": page_size},
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
