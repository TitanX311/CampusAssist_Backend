"""
Feed Service FastAPI application.

Startup:
  - Creates the feed_interactions table if not present.
  - Wires up health and feed routers.

OpenAPI spec:
  Available at /api/feed/openapi.json when DEBUG=true (for docs-service aggregation).
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from feed.cache import close as redis_close
from feed.config.database import engine
from feed.config.settings import get_settings
from feed.models import Base
from feed.routes import feed_router, health_router

settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Graceful shutdown: close Redis pool
    await redis_close()


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Personalised post feed for USER-type accounts. "
        "Fetches posts from all communities the user is a member of, "
        "ranks them by recency + engagement, caches in Redis, "
        "and tracks seen state in PostgreSQL."
    ),
    version="1.0.0",
    docs_url="/api/feed/docs" if settings.DEBUG else None,
    redoc_url="/api/feed/redoc" if settings.DEBUG else None,
    openapi_url=None,  # served manually below when DEBUG=true
    lifespan=lifespan,
)

# Mount routers
app.include_router(health_router)
app.include_router(feed_router)


# ---------------------------------------------------------------------------
# Custom OpenAPI endpoint (DEBUG only) — consumed by docs_service
# ---------------------------------------------------------------------------
if settings.DEBUG:
    @app.get("/api/feed/openapi.json", include_in_schema=False)
    async def openapi_json() -> dict[str, Any]:
        return get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
