from datetime import datetime

from pydantic import BaseModel, Field


class FeedItem(BaseModel):
    """A single post entry in the personalised My Feed."""

    post_id: str
    community_id: str
    user_id: str
    content: str
    likes: int
    views: int
    comment_count: int
    attachments: list[str]
    # Composite score: recency (0–10) + engagement (likes×3 + comments×2 + views×0.05)
    score: float
    created_at: datetime
    seen: bool = False


class FeedResponse(BaseModel):
    """Paginated My Feed response."""

    items: list[FeedItem]
    # Opaque cursor to pass as ?cursor= for the next page; null on last page.
    next_cursor: str | None = None
    # Total posts in the ranked list (pre-pagination).
    total_in_cache: int
    # True when the feed was rebuilt fresh on this request (cache miss).
    built_fresh: bool


class IndiaFeedItem(BaseModel):
    """A single post entry in the Across-India trending feed."""

    post_id: str
    community_id: str
    user_id: str
    content: str
    likes: int
    views: int
    comment_count: int
    attachments: list[str]
    # Engagement-first score: likes×5 + comments×3 + views×0.1 + recency bonus (0–3)
    score: float
    created_at: datetime


class IndiaFeedResponse(BaseModel):
    """Paginated Across-India feed response."""

    items: list[IndiaFeedItem]
    next_cursor: str | None = None
    total_in_cache: int
    built_fresh: bool


class SeenResponse(BaseModel):
    post_id: str
    status: str = "seen"


class InvalidateCacheResponse(BaseModel):
    status: str = "cache invalidated"
