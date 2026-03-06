"""
Campus Assist — Search Service

FastAPI application that indexes colleges and communities into a
local PostgreSQL database with full-text search (tsvector + GIN index)
and trigram similarity (pg_trgm) for fuzzy matching.

Startup sequence:
  1. Create tables (Base.metadata.create_all)
  2. Install pg_trgm and unaccent PostgreSQL extensions
  3. Launch background re-sync task (if SYNC_INTERVAL_SECONDS > 0)

Search is available unauthenticated; sync requires a valid JWT.
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from search.config.database import AsyncSessionLocal, engine
from search.config.settings import get_settings
from search.models.base import Base
from search.models.index import CollegeIndex, CommunityIndex  # noqa: F401 — register tables
from search.routes.health import router as health_router
from search.routes.search import router as search_router
from search.routes.sync import router as sync_router
from search.sync.syncer import background_sync_loop
from search.cache.backend import init_cache, close_cache

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── 1. Schema + extensions ───────────────────────────────────────────────
    async with engine.begin() as conn:
        # pg_trgm: GIN trigram indexes
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        # unaccent: normalise accented characters in FTS
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema ready")

    # ── 2. Redis cache ───────────────────────────────────────────────────────
    await init_cache(settings.REDIS_URL)
    logger.info("Redis cache ready")

    # ── 3. Background sync loop ──────────────────────────────────────────────
    sync_task = asyncio.create_task(
        background_sync_loop(settings, AsyncSessionLocal),
        name="search-sync-loop",
    )
    logger.info("Background sync task started")

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────────
    sync_task.cancel()
    try:
        await sync_task
    except asyncio.CancelledError:
        pass
    await close_cache()
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/api/search/docs" if settings.DEBUG else None,
    redoc_url="/api/search/redoc" if settings.DEBUG else None,
    openapi_url="/api/search/openapi.json" if settings.DEBUG else None,
)

app.include_router(health_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(sync_router, prefix="/api")
