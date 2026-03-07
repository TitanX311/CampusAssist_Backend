"""
Admin panel — college management.
Proxies to college_service admin routes.

GET    /admin/colleges           — list all colleges (filterable by search)
GET    /admin/colleges/{id}      — get a college by ID
POST   /admin/colleges           — create a college
PATCH  /admin/colleges/{id}      — update a college
DELETE /admin/colleges/{id}      — force-delete any college
"""
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from admin.config.settings import Settings, get_settings
from admin.dependencies.auth import TokenPayload, require_super_admin
from admin.http.client import api_delete, api_get, api_patch, api_post, raise_for_upstream

router = APIRouter(prefix="/admin/colleges", tags=["Admin Colleges"])


class CreateCollegeBody(BaseModel):
    name: str
    contact_email: str
    physical_address: str
    admin_users: list[str] = []


class UpdateCollegeBody(BaseModel):
    name: str | None = None
    contact_email: str | None = None
    physical_address: str | None = None


@router.get(
    "",
    summary="[Admin] List all colleges",
    description="Returns every college. `search` filters by name (case-insensitive). Requires SUPER_ADMIN role.",
)
async def list_colleges(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_get(
        f"{settings.COLLEGE_SERVICE_URL}/api/college/admin/list",
        request,
        {"page": page, "page_size": page_size},
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


@router.get(
    "/{college_id}",
    summary="[Admin] Get a college by ID",
    description="Returns a college record by ID. Requires SUPER_ADMIN role.",
)
async def get_college(
    college_id: str,
    request: Request,
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_get(
        f"{settings.COLLEGE_SERVICE_URL}/api/college/{college_id}",
        request,
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


@router.post(
    "",
    summary="[Admin] Create a college",
    description="Create a new college on behalf of any user. Requires SUPER_ADMIN role.",
    status_code=201,
)
async def create_college(
    body: CreateCollegeBody,
    request: Request,
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_post(
        f"{settings.COLLEGE_SERVICE_URL}/api/college",
        request,
        body.model_dump(),
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


@router.patch(
    "/{college_id}",
    summary="[Admin] Update a college",
    description="Update name, contact email, or address. Requires SUPER_ADMIN role.",
)
async def update_college(
    college_id: str,
    body: UpdateCollegeBody,
    request: Request,
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_patch(
        f"{settings.COLLEGE_SERVICE_URL}/api/college/admin/{college_id}",
        request,
        body.model_dump(exclude_none=True),
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


@router.delete(
    "/{college_id}",
    summary="[Admin] Force-delete any college",
    description=(
        "Permanently deletes a college bypassing the college-admin check. "
        "Requires SUPER_ADMIN role."
    ),
)
async def delete_college(
    college_id: str,
    request: Request,
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_delete(
        f"{settings.COLLEGE_SERVICE_URL}/api/college/admin/{college_id}",
        request,
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)
