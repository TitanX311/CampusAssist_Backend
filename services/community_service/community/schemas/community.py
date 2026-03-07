import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from community.models.community import CommunityType


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class CreateCommunityRequest(BaseModel):
    """Create a new community."""

    name: str = Field(min_length=3, max_length=100, description="Unique community name")
    type: CommunityType = Field(
        default=CommunityType.PUBLIC,
        description="PUBLIC — anyone can join. PRIVATE — join requires approval.",
    )
    parent_colleges: list[uuid.UUID] = Field(
        default_factory=list,
        description="UUIDs of college entities this community belongs to",
    )


class UpdateCommunityRequest(BaseModel):
    """Partial update — only supplied fields are changed."""

    name: str | None = Field(default=None, min_length=3, max_length=100)
    type: CommunityType | None = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class CommunityResponse(BaseModel):
    """Full community representation returned by the API.

    Viewer-context fields (``is_member``, ``is_requested``) are ``None`` when
    the endpoint does not receive an authenticated viewer (e.g. public listing).
    They are populated from the ``CommunityMember`` / ``CommunityJoinRequest``
    join tables — always a single indexed lookup per request, never N+1.
    """

    id: str
    name: str
    type: str
    parent_colleges: list[uuid.UUID]
    posts: list[uuid.UUID]

    # Denormalized counters — updated atomically alongside join table writes.
    member_count: int = 0
    post_count: int = 0

    # Viewer-context fields — populated when the caller is authenticated.
    is_member: bool | None = None
    is_requested: bool | None = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CommunityListResponse(BaseModel):
    """Paginated list of communities."""

    items: list[CommunityResponse]
    total: int
    page: int
    page_size: int


class JoinCommunityResponse(BaseModel):
    """Result of a join / join-request action."""

    community_id: str
    # 'joined' — user is now an active member (PUBLIC community)
    # 'requested' — user is in the pending list (PRIVATE community)
    status: str
    message: str


class LeaveCommunityResponse(BaseModel):
    """Result of a leave action."""

    community_id: str
    message: str


class PendingRequestsResponse(BaseModel):
    """Pending join requests for a PRIVATE community."""

    community_id: str
    requested_users: list[uuid.UUID]
    total: int


class ApproveRejectResponse(BaseModel):
    """Result of an approve or reject action on a join request."""

    community_id: str
    user_id: str
    message: str
