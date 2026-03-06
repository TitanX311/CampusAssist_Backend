"""
Admin-only comment management routes — gated by require_super_admin.

GET    /comments/admin/list     — list ALL comments (no community/membership filter)
GET    /comments/admin/{id}     — get any comment by ID (no membership check)
DELETE /comments/admin/{id}     — force-delete any comment (skips ownership,
                                  notifies post_service best-effort)
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from comment.config.database import get_db
from comment.config.settings import get_settings
from comment.dependencies.admin import require_super_admin
from comment.dependencies.auth import TokenPayload
from comment.grpc import clients as grpc_clients
from comment.repositories.comment_repository import CommentRepository
from comment.schemas.comment import (
    CommentListResponse,
    CommentResponse,
    DeleteCommentResponse,
)

logger = logging.getLogger(__name__)

admin_router = APIRouter(prefix="/comments/admin", tags=["Comments Admin"])


@admin_router.get(
    "/list",
    response_model=CommentListResponse,
    summary="[Admin] List all comments",
    description="Returns every comment across all posts. Requires SUPER_ADMIN role.",
)
async def list_all_comments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> CommentListResponse:
    repo = CommentRepository(db)
    items, total = await repo.get_all(page=page, page_size=page_size)
    return CommentListResponse(
        items=[CommentResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@admin_router.get(
    "/{comment_id}",
    response_model=CommentResponse,
    summary="[Admin] Get any comment by ID",
    description="Returns a comment without checking community membership. Requires SUPER_ADMIN role.",
)
async def admin_get_comment(
    comment_id: str,
    _: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    repo = CommentRepository(db)
    comment = await repo.get_by_id(comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")
    return CommentResponse.model_validate(comment)


@admin_router.delete(
    "/{comment_id}",
    response_model=DeleteCommentResponse,
    status_code=status.HTTP_200_OK,
    summary="[Admin] Force-delete any comment",
    description=(
        "Permanently deletes a comment regardless of ownership. "
        "Notifies post_service via gRPC best-effort. "
        "Requires SUPER_ADMIN role."
    ),
)
async def admin_delete_comment(
    comment_id: str,
    _: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> DeleteCommentResponse:
    repo = CommentRepository(db)
    comment = await repo.get_by_id(comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")

    post_id = str(comment.post_id)
    await repo.delete(comment)

    # Best-effort: notify post_service to remove comment UUID from post
    try:
        await grpc_clients.remove_comment(
            target=get_settings().POST_GRPC_TARGET,
            post_id=post_id,
            comment_id=comment_id,
        )
    except Exception as exc:
        logger.warning("admin_delete_comment: post notification failed: %s", exc)

    return DeleteCommentResponse(comment_id=comment_id, message="Comment deleted by admin.")
