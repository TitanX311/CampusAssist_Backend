from contextlib import asynccontextmanager

from fastapi import FastAPI

from comment.config.database import engine
from comment.config.settings import get_settings
from comment.models.base import Base
from comment.models.comment import Comment  # noqa: F401 — registers table with metadata
from comment.routes.health import router as health_router
from comment.routes.comment import router as comment_router
from comment.routes.admin import admin_router
from comment.grpc import clients as grpc_clients


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await grpc_clients.close_all()
    await engine.dispose()


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/api/comments/docs" if settings.DEBUG else None,
    redoc_url="/api/comments/redoc" if settings.DEBUG else None,
    openapi_url="/api/comments/openapi.json" if settings.DEBUG else None,
)

app.include_router(health_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(comment_router, prefix="/api")
