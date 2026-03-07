from contextlib import asynccontextmanager

from fastapi import FastAPI

from post.config.database import engine
from post.config.settings import get_settings
from post.models.base import Base
from post.models.post import Post  # noqa: F401 — registers table with metadata
from post.routes.health import router as health_router
from post.routes.post import router as post_router
from post.routes.admin import admin_router
from post.routes.internal import router as internal_router
from post.grpc import server as grpc_server
from post.grpc import community_client
from post.grpc import attachment_client
from post.grpc import auth_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    _settings = get_settings()
    await grpc_server.serve(_settings.GRPC_PORT)
    yield
    await grpc_server.stop()
    await community_client.close()
    await attachment_client.close()
    await auth_client.close()
    await engine.dispose()


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/api/posts/docs" if settings.DEBUG else None,
    redoc_url="/api/posts/redoc" if settings.DEBUG else None,
    openapi_url="/api/posts/openapi.json" if settings.DEBUG else None,
)

app.include_router(health_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(post_router, prefix="/api")
app.include_router(internal_router)
