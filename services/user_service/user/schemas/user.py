from datetime import datetime

from pydantic import BaseModel


class UserStatsResponse(BaseModel):
    """Aggregated activity counts for a user."""

    post_count: int = 0
    comment_count: int = 0
    community_count: int = 0


class UserProfileResponse(BaseModel):
    """Full public profile with stats."""

    user_id: str
    email: str | None = None
    name: str | None = None
    picture: str | None = None
    user_type: str
    is_active: bool
    joined_at: datetime | None = None
    stats: UserStatsResponse

    model_config = {"from_attributes": True}
