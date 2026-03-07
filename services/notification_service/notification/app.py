from contextlib import asynccontextmanager

from fastapi import FastAPI

from notification.config.database import engine
from notification.config.settings import get_settings
from notification.models.base import Base
from notification.models.notification import Notification  # noqa: F401 — registers table
from notification.routes.health import router as health_router
from notification.routes.notification import router as notification_router
from notification.grpc import server as grpc_server


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Start the gRPC server in the same process (non-blocking background task)
    _settings = get_settings()
    await grpc_server.serve(_settings.GRPC_PORT)
    yield
    # Graceful shutdown
    await grpc_server.stop()
    await engine.dispose()


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/api/notifications/docs" if settings.DEBUG else None,
    redoc_url="/api/notifications/redoc" if settings.DEBUG else None,
    openapi_url="/api/notifications/openapi.json" if settings.DEBUG else None,
)

app.include_router(health_router, prefix="/api")
app.include_router(notification_router, prefix="/api")
