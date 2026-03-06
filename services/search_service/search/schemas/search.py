from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class SearchResultItem(BaseModel):
    """A single hit — either a college or a community."""

    id: str
    name: str
    type: Literal["college", "community"]
    score: float

    # College fields (None when type == "community")
    contact_email: str | None = None
    physical_address: str | None = None
    community_count: int | None = None

    # Community fields (None when type == "college")
    community_type: Literal["PUBLIC", "PRIVATE"] | None = None
    parent_colleges: list[str] | None = None
    member_count: int | None = None


class SearchResponse(BaseModel):
    query: str
    type_filter: str
    items: list[SearchResultItem]
    total: int
    page: int
    page_size: int
    index_stats: dict | None = None


class SyncResponse(BaseModel):
    status: str
    colleges_indexed: int
    communities_indexed: int
    errors: list[str]
    duration_seconds: float
