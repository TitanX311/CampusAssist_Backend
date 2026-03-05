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
    """Full community representation returned by the API."""

    id: str
    name: str
    type: str
    member_users: list[uuid.UUID]
    requested_users: list[uuid.UUID]
    parent_colleges: list[uuid.UUID]
    posts: list[uuid.UUID]
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
