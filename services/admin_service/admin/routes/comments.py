"""
Admin panel — comment management.
Proxies to comment_service admin routes.

GET    /admin/comments           — list all comments
GET    /admin/comments/{id}      — get any comment (no membership check)
DELETE /admin/comments/{id}      — force-delete any comment
"""
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from admin.config.settings import Settings, get_settings
from admin.dependencies.auth import TokenPayload, require_super_admin
from admin.http.client import api_delete, api_get, raise_for_upstream

router = APIRouter(prefix="/admin/comments", tags=["Admin Comments"])


@router.get(
    "",
    summary="[Admin] List all comments",
    description="Returns every comment across all posts. Requires SUPER_ADMIN role.",
)
async def list_comments(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_get(
        f"{settings.COMMENT_SERVICE_URL}/api/comments/admin/list",
        request,
        {"page": page, "page_size": page_size},
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


@router.get(
    "/{comment_id}",
    summary="[Admin] Get any comment by ID",
    description="Returns a comment without membership checks. Requires SUPER_ADMIN role.",
)
async def get_comment(
    comment_id: str,
    request: Request,
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_get(
        f"{settings.COMMENT_SERVICE_URL}/api/comments/admin/{comment_id}",
        request,
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


@router.delete(
    "/{comment_id}",
    summary="[Admin] Force-delete any comment",
    description="Permanently deletes a comment regardless of ownership. Requires SUPER_ADMIN role.",
)
async def delete_comment(
    comment_id: str,
    request: Request,
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_delete(
        f"{settings.COMMENT_SERVICE_URL}/api/comments/admin/{comment_id}",
        request,
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)
