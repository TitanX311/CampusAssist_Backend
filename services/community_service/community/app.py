from contextlib import asynccontextmanager

from fastapi import FastAPI

from community.config.database import engine
from community.config.settings import get_settings
from community.models.base import Base
from community.models.community import Community  # noqa: F401 — registers table with metadata
from community.routes.community import router as community_router
from community.routes.admin import admin_router
from community.routes.health import router as health_router
from community.routes.internal import router as internal_router
from community.grpc import server as grpc_server
from community.grpc import college_client
from community.grpc import auth_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    _settings = get_settings()
    await grpc_server.serve(_settings.GRPC_PORT)
    yield
    await grpc_server.stop()
    await college_client.close()
    await auth_client.close()
    await engine.dispose()


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/api/community/docs" if settings.DEBUG else None,
    redoc_url="/api/community/redoc" if settings.DEBUG else None,
    openapi_url="/api/community/openapi.json" if settings.DEBUG else None,
)

app.include_router(health_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(community_router, prefix="/api")
app.include_router(internal_router)
