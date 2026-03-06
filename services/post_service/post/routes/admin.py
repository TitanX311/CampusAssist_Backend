"""
Admin-only post management routes — gated by require_super_admin.

GET    /posts/admin/list        — list ALL posts (no community/membership filter)
GET    /posts/admin/{id}        — get any post by ID (no membership check)
DELETE /posts/admin/{id}        — force-delete any post (skips ownership + attachment cleanup
                                  is best-effort via gRPC, non-fatal)
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from post.config.database import get_db
from post.config.settings import get_settings
from post.dependencies.admin import require_super_admin
from post.dependencies.auth import TokenPayload
from post.grpc import attachment_client
from post.repositories.post_repository import PostRepository
from post.schemas.post import DeletePostResponse, PostListResponse, PostResponse

logger = logging.getLogger(__name__)

admin_router = APIRouter(prefix="/posts/admin", tags=["Posts Admin"])


@admin_router.get(
    "/list",
    response_model=PostListResponse,
    summary="[Admin] List all posts",
    description="Returns every post across all communities. Requires SUPER_ADMIN role.",
)
async def list_all_posts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> PostListResponse:
    repo = PostRepository(db)
    items, total = await repo.get_all(page=page, page_size=page_size)
    return PostListResponse(
        items=[PostResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@admin_router.get(
    "/{post_id}",
    response_model=PostResponse,
    summary="[Admin] Get any post by ID",
    description="Returns a post without checking community membership. Requires SUPER_ADMIN role.",
)
async def admin_get_post(
    post_id: str,
    _: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    repo = PostRepository(db)
    post = await repo.get_by_id(post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    return PostResponse.model_validate(post)


@admin_router.delete(
    "/{post_id}",
    response_model=DeletePostResponse,
    status_code=status.HTTP_200_OK,
    summary="[Admin] Force-delete any post",
    description=(
        "Permanently deletes a post regardless of ownership. "
        "Attachment cleanup via gRPC is best-effort (non-fatal). "
        "Requires SUPER_ADMIN role."
    ),
)
async def admin_delete_post(
    post_id: str,
    _admin: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> DeletePostResponse:
    repo = PostRepository(db)
    post = await repo.get_by_id(post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")

    # Best-effort attachment cleanup (skip ownership check)
    attachment_ids = [str(a) for a in (post.attachments or [])]
    if attachment_ids:
        try:
            await attachment_client.delete_attachments(
                get_settings().ATTACHMENT_GRPC_TARGET,
                attachment_ids,
                str(post.user_id),  # pass original owner so MinIO key resolves correctly
            )
        except Exception as exc:
            logger.warning("admin_delete_post: attachment cleanup failed for %s: %s", post_id, exc)

    await repo.delete(post)
    return DeletePostResponse(post_id=post_id, message="Post deleted by admin.")
