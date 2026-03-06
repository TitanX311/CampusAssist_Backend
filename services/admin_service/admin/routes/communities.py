"""
Admin panel — community management.
Proxies to community_service admin routes.

GET    /admin/communities           — list all communities
GET    /admin/communities/{id}      — get a community by ID
DELETE /admin/communities/{id}      — force-delete a community
"""
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from admin.config.settings import Settings, get_settings
from admin.dependencies.auth import TokenPayload, require_super_admin
from admin.http.client import api_delete, api_get, raise_for_upstream

router = APIRouter(prefix="/admin/communities", tags=["Admin Communities"])


@router.get(
    "",
    summary="[Admin] List all communities",
    description="Returns every community regardless of membership. Requires SUPER_ADMIN role.",
)
async def list_communities(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_get(
        f"{settings.COMMUNITY_SERVICE_URL}/api/community/admin/list",
        request,
        {"page": page, "page_size": page_size},
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


@router.get(
    "/{community_id}",
    summary="[Admin] Get a community by ID",
    description="Returns a community record by ID. Requires SUPER_ADMIN role.",
)
async def get_community(
    community_id: str,
    request: Request,
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_get(
        f"{settings.COMMUNITY_SERVICE_URL}/api/community/{community_id}",
        request,
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


@router.delete(
    "/{community_id}",
    summary="[Admin] Force-delete a community",
    description="Permanently deletes any community. Requires SUPER_ADMIN role.",
)
async def delete_community(
    community_id: str,
    request: Request,
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_delete(
        f"{settings.COMMUNITY_SERVICE_URL}/api/community/admin/{community_id}",
        request,
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)
