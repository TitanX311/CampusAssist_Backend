"""
Post routes for post_service.

All mutating and read operations require:
  1. A valid Bearer access token (authenticated user).
  2. The authenticated user to be an active member of the target community.
     This is enforced by calling community_service's GET /api/community/{id}
     and checking that the user's UUID is in the `member_users` list.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from post.config.database import get_db
from post.config.settings import get_settings
from post.dependencies.auth import TokenPayload, get_current_user
from post.dependencies.community import assert_community_member
from post.grpc import attachment_client
from post.repositories.post_repository import PostRepository
from post.schemas.post import (
    CreatePostRequest,
    DeletePostResponse,
    PostListResponse,
    PostResponse,
    UpdatePostRequest,
)

router = APIRouter(prefix="/posts", tags=["Posts"])


class _AddCommentBody(BaseModel):
    """Internal — body for the comment registration endpoint."""
    comment_id: str

_POST_EXAMPLE = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "community_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "content": "Hello community!",
    "likes": 0,
    "views": 0,
    "attachments": [],
    "comments": [],
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
_ERROR_404_POST = {
    "description": "Not Found — post with the given ID does not exist",
    "content": {"application/json": {"example": {"detail": "Post not found."}}},
}
_ERROR_404_COMMUNITY = {
    "description": "Not Found — community with the given ID does not exist",
    "content": {"application/json": {"example": {"detail": "Community not found."}}},
}


# ---------------------------------------------------------------------------
# GET /posts/community/{community_id}  — list posts in a community
# ---------------------------------------------------------------------------

@router.get(
    "/community/{community_id}",
    response_model=PostListResponse,
    summary="List posts in a community",
    description=(
        "Returns a paginated list of posts in the given community, ordered by "
        "most recent first.\n\n"
        "**Membership required:** the authenticated user must be an active member "
        "of the community.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Paginated list of posts",
            "content": {
                "application/json": {
                    "example": {
                        "items": [_POST_EXAMPLE],
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
async def list_community_posts(
    community_id: str,
    request: Request,
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PostListResponse:
    await assert_community_member(community_id, current_user)

    repo = PostRepository(db)
    items, total = await repo.get_by_community(
        community_id=community_id,
        page=page,
        page_size=page_size,
    )
    return PostListResponse(
        items=[PostResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# GET /posts/{post_id}  — get a single post
# ---------------------------------------------------------------------------

@router.get(
    "/{post_id}",
    response_model=PostResponse,
    summary="Get a post by ID",
    description=(
        "Returns the full post object and increments the view counter.\n\n"
        "**Membership required:** the authenticated user must be a member of the "
        "community the post belongs to.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Post details",
            "content": {"application/json": {"example": _POST_EXAMPLE}},
        },
        401: _ERROR_401,
        403: _ERROR_403,
        404: _ERROR_404_POST,
    },
)
async def get_post(
    post_id: str,
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    repo = PostRepository(db)
    post = await repo.get_by_id(post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")

    await assert_community_member(str(post.community_id), current_user)

    post = await repo.increment_views(post)
    return PostResponse.model_validate(post)


# ---------------------------------------------------------------------------
# POST /posts  — create a post
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a post",
    description=(
        "Create a new post inside the specified community.\n\n"
        "**Membership required:** the authenticated user must be an active member "
        "of the target community.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        201: {
            "description": "Post created successfully",
            "content": {"application/json": {"example": _POST_EXAMPLE}},
        },
        401: _ERROR_401,
        403: _ERROR_403,
        404: _ERROR_404_COMMUNITY,
    },
)
async def create_post(
    body: CreatePostRequest,
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    await assert_community_member(str(body.community_id), current_user)

    # --- Atomicity: validate attachments belong to the caller before writing ---
    attachment_ids = [str(a) for a in body.attachments]
    if attachment_ids:
        target = get_settings().ATTACHMENT_GRPC_TARGET
        try:
            valid, invalid_ids = await attachment_client.validate_attachments(
                target, attachment_ids, current_user.user_id
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Could not reach attachment service. Try again later.",
            )
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid or unauthorized attachment IDs: {invalid_ids}",
            )

    repo = PostRepository(db)
    post = await repo.create(
        user_id=current_user.user_id,
        community_id=str(body.community_id),
        content=body.content,
        attachments=body.attachments,
    )
    return PostResponse.model_validate(post)


# ---------------------------------------------------------------------------
# PATCH /posts/{post_id}  — update a post
# ---------------------------------------------------------------------------

@router.patch(
    "/{post_id}",
    response_model=PostResponse,
    summary="Update a post",
    description=(
        "Partially update a post's `content` or `attachments`.\n\n"
        "**Ownership required:** only the author of the post can update it.\n\n"
        "**Membership required:** the authenticated user must still be a member "
        "of the community the post belongs to.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Updated post",
            "content": {"application/json": {"example": _POST_EXAMPLE}},
        },
        401: _ERROR_401,
        403: _ERROR_403,
        404: _ERROR_404_POST,
    },
)
async def update_post(
    post_id: str,
    body: UpdatePostRequest,
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    repo = PostRepository(db)
    post = await repo.get_by_id(post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")

    await assert_community_member(str(post.community_id), current_user)

    if str(post.user_id) != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own posts.",
        )

    # --- Atomicity: validate new attachments and remove dropped ones ---
    if body.attachments is not None:
        new_ids  = {str(a) for a in body.attachments}
        old_ids  = {str(a) for a in (post.attachments or [])}
        added    = new_ids - old_ids
        removed  = old_ids - new_ids
        target   = get_settings().ATTACHMENT_GRPC_TARGET

        if added:
            try:
                valid, invalid_ids = await attachment_client.validate_attachments(
                    target, list(added), current_user.user_id
                )
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Could not reach attachment service. Try again later.",
                )
            if not valid:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid or unauthorized attachment IDs: {invalid_ids}",
                )

        # Commit the post update first, then clean up removed attachments.
        post = await repo.update(post, content=body.content, attachments=body.attachments)

        if removed:
            try:
                await attachment_client.delete_attachments(
                    target, list(removed), current_user.user_id
                )
            except Exception:
                # Best-effort: log but don't fail the request since the post
                # update already succeeded.  Orphaned files can be swept later.
                import logging
                logging.getLogger(__name__).warning(
                    "update_post: failed to delete removed attachments %s", removed
                )
    else:
        post = await repo.update(post, content=body.content, attachments=body.attachments)

    return PostResponse.model_validate(post)


# ---------------------------------------------------------------------------
# DELETE /posts/{post_id}  — delete a post
# ---------------------------------------------------------------------------

@router.delete(
    "/{post_id}",
    response_model=DeletePostResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a post",
    description=(
        "Permanently delete a post.\n\n"
        "**Ownership required:** only the author of the post can delete it.\n\n"
        "**Membership required:** the authenticated user must be a member of the "
        "community the post belongs to.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Post deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "post_id": "550e8400-e29b-41d4-a716-446655440000",
                        "message": "Post deleted successfully.",
                    }
                }
            },
        },
        401: _ERROR_401,
        403: _ERROR_403,
        404: _ERROR_404_POST,
    },
)
async def delete_post(
    post_id: str,
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeletePostResponse:
    repo = PostRepository(db)
    post = await repo.get_by_id(post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")

    await assert_community_member(str(post.community_id), current_user)

    if str(post.user_id) != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own posts.",
        )

    # --- Atomicity: delete attachments from attachment_service first so that
    #     if this fails the post record is still intact (no dangling UUID refs).
    attachment_ids = [str(a) for a in (post.attachments or [])]
    if attachment_ids:
        target = get_settings().ATTACHMENT_GRPC_TARGET
        try:
            success, message, failed_ids = await attachment_client.delete_attachments(
                target, attachment_ids, current_user.user_id
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Could not reach attachment service. Try again later.",
            )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Could not delete attachments: {message} (failed: {failed_ids})",
            )

    await repo.delete(post)
    return DeletePostResponse(post_id=post_id, message="Post deleted successfully.")


# ---------------------------------------------------------------------------
# Like stub (not yet implemented)
# ---------------------------------------------------------------------------

@router.post(
    "/{post_id}/like",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Like / unlike a post (not implemented)",
    description="Toggle a like on a post. **Not yet implemented.**",
    include_in_schema=True,
)
async def like_post(post_id: str) -> dict:  # noqa: ARG001
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint is not yet implemented.",
    )


@router.post(
    "/{post_id}/comments",
    response_model=PostResponse,
    status_code=status.HTTP_200_OK,
    summary="Register a comment on a post",
    description=(
        "Appends `comment_id` to the post's `comments` UUID array.\n\n"
        "Called internally by **comment_service** after a comment is persisted. "
        "Requires the caller to be an authenticated community member.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Post with updated comments list",
            "content": {"application/json": {"example": _POST_EXAMPLE}},
        },
        401: _ERROR_401,
        403: _ERROR_403,
        404: _ERROR_404_POST,
    },
)
async def add_comment(
    post_id: str,
    body: _AddCommentBody,
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    repo = PostRepository(db)
    post = await repo.get_by_id(post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")

    await assert_community_member(str(post.community_id), current_user, request)

    post = await repo.add_comment(post, str(body.comment_id))
    return PostResponse.model_validate(post)


@router.delete(
    "/{post_id}/comments/{comment_id}",
    response_model=PostResponse,
    status_code=status.HTTP_200_OK,
    summary="Unregister a comment from a post",
    description=(
        "Removes `comment_id` from the post's `comments` UUID array.\n\n"
        "Called internally by **comment_service** when a comment is deleted. "
        "Requires the caller to be an authenticated community member.\n\n"
        "**Authentication:** `Authorization: Bearer <access_token>` header required."
    ),
    responses={
        200: {
            "description": "Post with updated comments list",
            "content": {"application/json": {"example": _POST_EXAMPLE}},
        },
        401: _ERROR_401,
        403: _ERROR_403,
        404: _ERROR_404_POST,
    },
)
async def delete_comment(
    post_id: str,
    comment_id: str,
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    repo = PostRepository(db)
    post = await repo.get_by_id(post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")

    await assert_community_member(str(post.community_id), current_user, request)

    post = await repo.remove_comment(post, comment_id)
    return PostResponse.model_validate(post)
