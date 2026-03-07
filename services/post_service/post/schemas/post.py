import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class CreatePostRequest(BaseModel):
    """Create a new post inside a community."""

    community_id: uuid.UUID = Field(description="UUID of the community this post belongs to")
    content: str = Field(min_length=1, max_length=10_000, description="Post body text")
    attachments: list[uuid.UUID] = Field(
        default_factory=list,
        description="UUIDs of attachment objects (resolved via attachment service)",
    )


class UpdatePostRequest(BaseModel):
    """Partial update — only supplied fields are changed."""

    content: str | None = Field(default=None, min_length=1, max_length=10_000)
    attachments: list[uuid.UUID] | None = Field(default=None)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class PostResponse(BaseModel):
    """Full post representation returned by the API.

    Viewer-context fields
    ----------------------
    ``liked_by_me`` — whether the calling user has liked this post.
    ``comment_count`` — number of comments (len of ``comments`` array).

    These are populated by the route handler from the ``PostLike`` join table
    in a single batch query — never N+1.  They are ``None`` when no viewer
    context is available (e.g. admin list endpoint).
    """

    id: str
    user_id: uuid.UUID
    community_id: uuid.UUID
    content: str
    likes: int
    views: int
    attachments: list[uuid.UUID]
    comments: list[uuid.UUID]
    comment_count: int = 0
    created_at: datetime
    updated_at: datetime
    # Populated at the HTTP layer via auth_service gRPC — not stored in this DB
    user_name: str | None = None
    user_picture: str | None = None
    # Viewer-context — populated when an authenticated caller is known
    liked_by_me: bool | None = None

    model_config = {"from_attributes": True}


class PostListResponse(BaseModel):
    """Paginated list of posts."""

    items: list[PostResponse]
    total: int
    page: int
    page_size: int


class DeletePostResponse(BaseModel):
    """Result of a delete action."""

    post_id: str
    message: str


class LikePostResponse(BaseModel):
    """Result of a like / unlike action."""

    post_id: str
    liked: bool         # True = now liked, False = now unliked
    likes: int          # updated total like count
    message: str

