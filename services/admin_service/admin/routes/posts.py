"""
Admin panel — post management.
Proxies to post_service admin routes.

GET    /admin/posts           — list all posts
GET    /admin/posts/{id}      — get any post (no membership check)
DELETE /admin/posts/{id}      — force-delete any post
"""
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from admin.config.settings import Settings, get_settings
from admin.dependencies.auth import TokenPayload, require_super_admin
from admin.http.client import api_delete, api_get, raise_for_upstream

router = APIRouter(prefix="/admin/posts", tags=["Admin Posts"])


@router.get(
    "",
    summary="[Admin] List all posts",
    description="Returns every post across all communities. Requires SUPER_ADMIN role.",
)
async def list_posts(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_get(
        f"{settings.POST_SERVICE_URL}/api/posts/admin/list",
        request,
        {"page": page, "page_size": page_size},
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


@router.get(
    "/{post_id}",
    summary="[Admin] Get any post by ID",
    description="Returns a post without membership checks. Requires SUPER_ADMIN role.",
)
async def get_post(
    post_id: str,
    request: Request,
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_get(
        f"{settings.POST_SERVICE_URL}/api/posts/admin/{post_id}",
        request,
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


@router.delete(
    "/{post_id}",
    summary="[Admin] Force-delete any post",
    description="Permanently deletes a post regardless of ownership. Requires SUPER_ADMIN role.",
)
async def delete_post(
    post_id: str,
    request: Request,
    _: TokenPayload = Depends(require_super_admin),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    resp = await api_delete(
        f"{settings.POST_SERVICE_URL}/api/posts/admin/{post_id}",
        request,
    )
    raise_for_upstream(resp)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)
