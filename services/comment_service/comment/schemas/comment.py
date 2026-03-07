import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class CreateCommentRequest(BaseModel):
    """Create a new comment on a post."""

    post_id: uuid.UUID = Field(description="UUID of the post being commented on")
    community_id: uuid.UUID = Field(description="UUID of the community the post belongs to")
    content: str = Field(min_length=1, max_length=5_000, description="Comment body text")


class UpdateCommentRequest(BaseModel):
    """Partial update — only supplied fields are changed."""

    content: str | None = Field(default=None, min_length=1, max_length=5_000)


class CreateReplyRequest(BaseModel):
    """Create a reply to an existing comment."""

    content: str = Field(min_length=1, max_length=5_000, description="Reply body text")


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class CommentResponse(BaseModel):
    """Full comment representation returned by the API."""

    id: str
    post_id: uuid.UUID
    user_id: uuid.UUID
    community_id: uuid.UUID
    parent_id: str | None
    content: str
    likes: int
    # liked_by_me is set at the HTTP layer by looking up the CommentLike join
    # table for the current viewer — never persisted on the Comment row.
    liked_by_me: bool | None = None
    # reply_count is derived at query time; 0 for replies (leaves).
    reply_count: int = 0
    created_at: datetime
    updated_at: datetime
    # Populated at the HTTP layer via auth_service gRPC — not stored in this DB
    user_name: str | None = None
    user_picture: str | None = None

    model_config = {"from_attributes": True}


class LikeCommentResponse(BaseModel):
    """Result of an explicit like or unlike action."""

    comment_id: str
    liked: bool   # True = like added, False = like removed
    likes: int    # updated total
    message: str


# Keep the old name as an alias so any existing callers still resolve.
LikeResponse = LikeCommentResponse


class CommentListResponse(BaseModel):
    """Paginated list of comments."""

    items: list[CommentResponse]
    total: int
    page: int
    page_size: int


class DeleteCommentResponse(BaseModel):
    """Result of a delete action."""

    comment_id: str
    message: str
