from contextlib import asynccontextmanager

from fastapi import FastAPI

from attachment.config.database import engine
from attachment.config.settings import get_settings
from attachment.models.base import Base
from attachment.models.attachment import Attachment  # noqa: F401 — registers table with metadata
from attachment.routes.health import router as health_router
from attachment.routes.attachment import router as attachment_router
from attachment.routes.admin import admin_router
from attachment.storage import minio_client as storage
from attachment.grpc import server as grpc_server
from attachment.grpc import auth_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Ensure MinIO bucket exists
    await storage.ensure_bucket()
    # Start gRPC server
    _settings = get_settings()
    await grpc_server.serve(_settings.GRPC_PORT)
    yield
    await grpc_server.stop()
    await auth_client.close()
    await engine.dispose()


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/api/attachments/docs" if settings.DEBUG else None,
    redoc_url="/api/attachments/redoc" if settings.DEBUG else None,
    openapi_url="/api/attachments/openapi.json" if settings.DEBUG else None,
)

app.include_router(health_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(attachment_router, prefix="/api")
