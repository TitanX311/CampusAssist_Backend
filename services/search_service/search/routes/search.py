"""
Search endpoint — GET /api/search

Query parameters:
  q          (required) — free-text query, 1–500 chars
  type       (default "all") — "college" | "community" | "all"
  college_id (optional) — filter communities by college (only when type=community|all)
  page       (default 1)
  page_size  (default 20, max 50)
"""
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from search.cache.backend import get_cache
from search.config.database import get_db
from search.config.settings import Settings, get_settings
from search.repositories.search_repository import SearchRepository
from search.schemas.search import SearchResponse, SearchResultItem

router = APIRouter(tags=["Search"])


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Search colleges and/or communities",
    description=(
        "Full-text + trigram search over indexed colleges and communities.\n\n"
        "Results are ranked by relevance (ts_rank + trigram similarity). "
        "Use `type` to restrict to a single entity type. "
        "Use `college_id` to scope community results to a specific college."
    ),
)
async def search(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    type: Literal["all", "college", "community"] = Query(
        default="all", description="Filter by entity type"
    ),
    college_id: str | None = Query(
        default=None,
        description="Restrict community results to a specific college ID",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SearchResponse:
    cache = get_cache()

    # ── Cache hit ────────────────────────────────────────────────────────────
    cached = await cache.get(q, type, college_id, page, page_size)
    if cached is not None:
        items_raw, total = cached
        return SearchResponse(
            query=q,
            type_filter=type,
            items=[SearchResultItem(**i) for i in items_raw],
            total=total,
            page=page,
            page_size=page_size,
        )

    # ── Cache miss — query DB ────────────────────────────────────────────────
    repo = SearchRepository(db)
    raw: list[dict] = []
    total = 0

    if type == "college":
        raw, total = await repo.search_colleges(q, page, page_size)
    elif type == "community":
        raw, total = await repo.search_communities(q, page, page_size, college_id)
    else:
        raw, total = await repo.search_all(q, page, page_size)

    # ── Store in cache ───────────────────────────────────────────────────────
    await cache.set(q, type, college_id, page, page_size, raw, total, settings.CACHE_TTL_SECONDS)

    return SearchResponse(
        query=q,
        type_filter=type,
        items=[SearchResultItem(**i) for i in raw],
        total=total,
        page=page,
        page_size=page_size,
    )
