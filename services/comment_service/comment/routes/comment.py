"""
Comment routes for comment_service.

All mutating and read operations require:
  1. A valid Bearer access token (authenticated user).
  2. The authenticated user to be an active member of the target community.
     This is enforced by calling community_service's GET /api/community/{id}
     and checking that the user's UUID is in the `member_users` list.

On comment creation the post_service is notified via an internal call to
  POST /api/posts/{post_id}/comments
so that the post's `comments` UUID array stays in sync.

On comment deletion the post_service is notified via
  DELETE /api/posts/{post_id}/comments/{comment_id}
"""

import grpc
import grpc.aio
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from comment.config.database import get_db
from comment.config.settings import get_settings
from comment.dependencies.auth import TokenPayload, get_current_user
from comment.dependencies.community import assert_community_member
from comment.repositories.comment_repository import CommentRepository
from comment.grpc import clients as grpc_clients
from comment.schemas.comment import (
    CommentListResponse,
    CommentResponse,
    CreateCommentRequest,
    CreateReplyRequest,
    DeleteCommentResponse,
    LikeResponse,
    UpdateCommentRequest,
)

router = APIRouter(prefix="/comments", tags=["Comments"])

_COMMENT_EXAMPLE = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "post_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "user_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "community_id": "c5e8f1a2-b3c4-d5e6-f7a8-b9c0d1e2f3a4",
    "content": "Great post!",
    "likes": 0,
    "replies": [],
    "created_at": "2026-03-01T10:00:00+00:00",
    "updated_at": "2026-03-01T10:00:00+00:00",
}

_ERROR_401 = {
    "description": "Unauthorized — missing, expired, or invalid Bearer access token",
    "content": {"application/json": {"example": {"detail": "Not authenticated."}}},
}
_ERROR_403 = {
    "description": "Forbidden — user is not a member of the community",
    "content": {"application/json": {"example": {"detail": "You are not a member of this community."}}},
}
_ERROR_404_COMMENT = {
    "description": "Not Found — comment with the given ID does not exist",
    "content": {"application/json": {"example": {"detail": "Comment not found."}}},
}
_ERROR_404_COMMUNITY = {
    "description": "Not Found — community with the given ID does not exist",
    "content": {"application/json": {"example": {"detail": "Community not found."}}},
}


async def _notify_post_add_comment(post_id: str, comment_id: str) -> None:
    """
    Notify post_service that a comment was created via gRPC.
    Failure is non-fatal.
    """
    settings = get_settings()
    try:
        await grpc_clients.add_comment(
            target=settings.POST_GRPC_TARGET,
            post_id=post_id,
            comment_id=comment_id,
        )
    except grpc.aio.AioRpcError:
        # Best-effort — do not fail the comment creation
        pass


async def _notify_post_remove_comment(post_id: str, comment_id: str) -> None:
    """
    Notify post_service that a comment was deleted via gRPC.
    Failure is non-fatal.
    """
    settings = get_settings()
    try:
        await grpc_clients.remove_comment(
            target=settings.POST_GRPC_TARGET,
            post_id=post_id,
            comment_id=comment_id,
        )
    except grpc.aio.AioRpcError:
        # Best-effort — do not fail the comment deletion
        pass


# ---------------------------------------------------------------------------
# GET /comments/post/{post_id}  — list comments for a post
# ---------------------------------------------------------------------------

@router.get(
    "/post/{post_id}",
    response_model=CommentListResponse,
    summary="List comments on a post",
    description=(
        "Returns a paginated list of comments on the given post, ordered by "
        "most recent first.\n\n"
        "**Membership required:** the authenticated user must be an active member "
        "of the community the post belongs to.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Paginated list of comments",
            "content": {
                "application/json": {
                    "example": {
                        "items": [_COMMENT_EXAMPLE],
                        "total": 1,
                        "page": 1,
                        "page_size": 20,
                    }
                }
            },
        },
        401: _ERROR_401,
        403: _ERROR_403,
        404: _ERROR_404_COMMUNITY,
    },
)
async def list_post_comments(
    post_id: str,
    community_id: str = Query(description="Community ID the post belongs to (required for membership check)"),
    request: Request = None,
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommentListResponse:
    await assert_community_member(community_id, current_user)

    repo = CommentRepository(db)
    items, total = await repo.get_by_post(
        post_id=post_id,
        page=page,
        page_size=page_size,
    )
    return CommentListResponse(
        items=[CommentResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# GET /comments/{comment_id}  — get a single comment
# ---------------------------------------------------------------------------

@router.get(
    "/{comment_id}",
    response_model=CommentResponse,
    summary="Get a comment by ID",
    description=(
        "Returns the full comment object.\n\n"
        "**Membership required:** the authenticated user must be a member of the "
        "community the comment belongs to.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Comment details",
            "content": {"application/json": {"example": _COMMENT_EXAMPLE}},
        },
        401: _ERROR_401,
        403: _ERROR_403,
        404: _ERROR_404_COMMENT,
    },
)
async def get_comment(
    comment_id: str,
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    repo = CommentRepository(db)
    comment = await repo.get_by_id(comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")

    await assert_community_member(str(comment.community_id), current_user)

    return CommentResponse.model_validate(comment)


# ---------------------------------------------------------------------------
# POST /comments  — create a comment
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a comment",
    description=(
        "Create a new comment on the specified post.\n\n"
        "**Membership required:** the authenticated user must be an active member "
        "of the target community.\n\n"
        "After the comment is persisted, post_service is notified so it can append "
        "the comment UUID to the post's `comments` array.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        201: {
            "description": "Comment created successfully",
            "content": {"application/json": {"example": _COMMENT_EXAMPLE}},
        },
        401: _ERROR_401,
        403: _ERROR_403,
        404: _ERROR_404_COMMUNITY,
    },
)
async def create_comment(
    body: CreateCommentRequest,
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    await assert_community_member(str(body.community_id), current_user)

    repo = CommentRepository(db)
    comment = await repo.create(
        post_id=str(body.post_id),
        user_id=current_user.user_id,
        community_id=str(body.community_id),
        content=body.content,
    )

    # Notify post_service — best-effort, non-blocking
    await _notify_post_add_comment(str(body.post_id), comment.id)

    return CommentResponse.model_validate(comment)


# ---------------------------------------------------------------------------
# PATCH /comments/{comment_id}  — update a comment
# ---------------------------------------------------------------------------

@router.patch(
    "/{comment_id}",
    response_model=CommentResponse,
    summary="Update a comment",
    description=(
        "Partially update a comment's `content`.\n\n"
        "**Ownership required:** only the author of the comment can update it.\n\n"
        "**Membership required:** the authenticated user must still be a member "
        "of the community.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Updated comment",
            "content": {"application/json": {"example": _COMMENT_EXAMPLE}},
        },
        401: _ERROR_401,
        403: _ERROR_403,
        404: _ERROR_404_COMMENT,
    },
)
async def update_comment(
    comment_id: str,
    body: UpdateCommentRequest,
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    repo = CommentRepository(db)
    comment = await repo.get_by_id(comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")

    await assert_community_member(str(comment.community_id), current_user)

    if str(comment.user_id) != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments.",
        )

    comment = await repo.update(comment, content=body.content)
    return CommentResponse.model_validate(comment)


# ---------------------------------------------------------------------------
# DELETE /comments/{comment_id}  — delete a comment
# ---------------------------------------------------------------------------

@router.delete(
    "/{comment_id}",
    response_model=DeleteCommentResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a comment",
    description=(
        "Permanently delete a comment.\n\n"
        "**Ownership required:** only the author of the comment can delete it.\n\n"
        "**Membership required:** the authenticated user must be a member of the "
        "community.\n\n"
        "After deletion, post_service is notified so it removes the comment UUID "
        "from the post's `comments` array.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Comment deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "comment_id": "550e8400-e29b-41d4-a716-446655440000",
                        "message": "Comment deleted successfully.",
                    }
                }
            },
        },
        401: _ERROR_401,
        403: _ERROR_403,
        404: _ERROR_404_COMMENT,
    },
)
async def delete_comment(
    comment_id: str,
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeleteCommentResponse:
    repo = CommentRepository(db)
    comment = await repo.get_by_id(comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")

    await assert_community_member(str(comment.community_id), current_user)

    if str(comment.user_id) != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments.",
        )

    post_id = str(comment.post_id)

    await repo.delete(comment)

    # Notify post_service — best-effort, non-blocking
    await _notify_post_remove_comment(post_id, comment_id)

    return DeleteCommentResponse(comment_id=comment_id, message="Comment deleted successfully.")


# ---------------------------------------------------------------------------
# Not-yet-implemented stubs
# ---------------------------------------------------------------------------

@router.post(
    "/{comment_id}/like",
    response_model=LikeResponse,
    status_code=status.HTTP_200_OK,
    summary="Like / unlike a comment",
    description=(
        "Toggle a like on a comment for the authenticated user.\n\n"
        "- If the user has **not** liked the comment, the like is **added**.\n"
        "- If the user has **already** liked the comment, the like is **removed**.\n\n"
        "**Membership required:** the user must be a member of the comment's community.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Like toggled",
            "content": {
                "application/json": {
                    "example": {
                        "comment_id": "550e8400-e29b-41d4-a716-446655440000",
                        "liked": True,
                        "likes": 1,
                    }
                }
            },
        },
        401: _ERROR_401,
        403: _ERROR_403,
        404: _ERROR_404_COMMENT,
    },
)
async def like_comment(
    comment_id: str,
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LikeResponse:
    repo = CommentRepository(db)
    comment = await repo.get_by_id(comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")

    await assert_community_member(str(comment.community_id), current_user)

    comment, liked = await repo.toggle_like(comment, current_user.user_id)
    return LikeResponse(comment_id=comment_id, liked=liked, likes=comment.likes)


@router.get(
    "/{comment_id}/replies",
    response_model=CommentListResponse,
    summary="List replies to a comment",
    description=(
        "Returns a paginated list of direct replies to the given comment, ordered "
        "oldest-first so threads read naturally top-to-bottom.\n\n"
        "Each reply has `parent_id` set to `comment_id`. To fetch nested replies, "
        "call this endpoint recursively with the reply's own `id`.\n\n"
        "**Membership required:** the user must be a member of the comment's community.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Paginated list of replies",
            "content": {
                "application/json": {
                    "example": {
                        "items": [{**_COMMENT_EXAMPLE, "parent_id": "550e8400-e29b-41d4-a716-446655440000"}],
                        "total": 1,
                        "page": 1,
                        "page_size": 20,
                    }
                }
            },
        },
        401: _ERROR_401,
        403: _ERROR_403,
        404: _ERROR_404_COMMENT,
    },
)
async def list_replies(
    comment_id: str,
    request: Request,
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommentListResponse:
    repo = CommentRepository(db)
    parent = await repo.get_by_id(comment_id)
    if parent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")

    await assert_community_member(str(parent.community_id), current_user)

    items, total = await repo.get_replies(
        parent_id=comment_id,
        page=page,
        page_size=page_size,
    )
    return CommentListResponse(
        items=[CommentResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/{comment_id}/replies",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Reply to a comment",
    description=(
        "Create a reply to an existing comment.\n\n"
        "The reply is stored as a new `Comment` row with `parent_id` pointing to "
        "the target comment. It inherits `post_id` and `community_id` from the parent "
        "so it lives in the same thread context.\n\n"
        "Replies are **not** registered directly on the post's `comments` array — "
        "only top-level comments are. Retrieve replies via "
        "`GET /api/comments/{comment_id}/replies`.\n\n"
        "**Membership required:** the user must be a member of the comment's community.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        201: {
            "description": "Reply created successfully",
            "content": {"application/json": {"example": _COMMENT_EXAMPLE}},
        },
        401: _ERROR_401,
        403: _ERROR_403,
        404: _ERROR_404_COMMENT,
    },
)
async def add_reply(
    comment_id: str,
    body: CreateReplyRequest,
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    repo = CommentRepository(db)
    parent = await repo.get_by_id(comment_id)
    if parent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")

    await assert_community_member(str(parent.community_id), current_user)

    reply = await repo.create_reply(
        parent=parent,
        user_id=current_user.user_id,
        content=body.content,
    )

    return CommentResponse.model_validate(reply)
