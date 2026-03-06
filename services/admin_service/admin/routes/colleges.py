"""
Admin panel — college management.
Proxies to college_service admin routes.

GET    /admin/colleges           — list all colleges
GET    /admin/colleges/{id}      — get a college by ID
DELETE /admin/colleges/{id}      — force-delete any college
"""
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from admin.config.settings import Settings, get_settings
from admin.dependencies.auth import TokenPayload, require_super_admin
from admin.http.client import api_delete, api_get, raise_for_upstream

router = APIRouter(prefix="/admin/colleges", tags=["Admin Colleges"])


@router.get(
    "",
    summary="[Admin] List all colleges",
    description="Returns every college. Requires SUPER_ADMIN role.",
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
