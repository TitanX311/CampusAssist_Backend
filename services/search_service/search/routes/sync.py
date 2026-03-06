"""
Sync endpoint — POST /api/search/sync

Triggers a full re-index from college and community services.
Requires a valid JWT (any authenticated user may trigger a sync).

Also exposes GET /api/search/stats for index health monitoring.
"""
import time

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from search.config.database import AsyncSessionLocal, get_db
from search.config.settings import get_settings, Settings
from search.dependencies.auth import TokenPayload, get_current_user
from search.repositories.search_repository import SearchRepository
from search.schemas.search import SyncResponse
from search.sync.syncer import sync_all

router = APIRouter(tags=["Sync"])


@router.post(
    "/search/sync",
    response_model=SyncResponse,
    summary="Trigger a full re-index",
    description=(
        "Fetches all colleges and communities from upstream services and "
        "rebuilds the search index. Requires authentication."
    ),
)
async def trigger_sync(
    _: TokenPayload = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> SyncResponse:
    t0 = time.monotonic()
    stats = await sync_all(settings, AsyncSessionLocal)
    return SyncResponse(
        status="ok" if not stats["errors"] else "partial",
        colleges_indexed=stats["colleges"],
        communities_indexed=stats["communities"],
        errors=stats["errors"],
        duration_seconds=stats.get("duration_seconds", round(time.monotonic() - t0, 2)),
    )


@router.get(
    "/search/stats",
    summary="Index statistics",
    description="Returns counts of indexed records and last-indexed timestamp.",
)
async def index_stats(
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    repo = SearchRepository(db)
    return JSONResponse(await repo.index_stats())
