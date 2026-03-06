"""
Admin panel — attachment management.
Proxies to attachment_service admin routes.

GET    /admin/attachments           — list all attachments
GET    /admin/attachments/{id}      — get attachment metadata
DELETE /admin/attachments/{id}      — force-delete any attachment (MinIO + DB)
"""
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from admin.config.settings import Settings, get_settings
from admin.dependencies.auth import TokenPayload, require_super_admin
from admin.http.client import api_delete, api_get, raise_for_upstream

router = APIRouter(prefix="/admin/attachments", tags=["Admin Attachments"])


@router.get(
    "",
    summary="[Admin] List all attachments",
    description="Returns every uploaded attachment regardless of uploader. Requires SUPER_ADMIN role.",
)
async def list_attachments(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_get(
        f"{settings.ATTACHMENT_SERVICE_URL}/api/attachments/admin/list",
        request,
        {"page": page, "page_size": page_size},
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


@router.get(
    "/{attachment_id}",
    summary="[Admin] Get attachment metadata",
    description="Returns attachment metadata by ID. Requires SUPER_ADMIN role.",
)
async def get_attachment(
    attachment_id: str,
    request: Request,
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_get(
        f"{settings.ATTACHMENT_SERVICE_URL}/api/attachments/{attachment_id}",
        request,
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


@router.delete(
    "/{attachment_id}",
    summary="[Admin] Force-delete any attachment",
    description=(
        "Removes the file from MinIO and its DB record regardless of uploader. "
        "Requires SUPER_ADMIN role."
    ),
)
async def delete_attachment(
    attachment_id: str,
    request: Request,
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_delete(
        f"{settings.ATTACHMENT_SERVICE_URL}/api/attachments/admin/{attachment_id}",
        request,
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)
