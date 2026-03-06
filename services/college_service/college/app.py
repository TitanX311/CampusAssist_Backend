from contextlib import asynccontextmanager

from fastapi import FastAPI

from college.config.database import engine
from college.config.settings import get_settings
from college.models.base import Base
from college.models.college import College  # noqa: F401 — registers table
from college.models.college_user import CollegeUser  # noqa: F401 — registers table
from college.routes.college import router as college_router
from college.routes.admin import admin_router
from college.routes.health import router as health_router
from college.grpc import server as grpc_server
from college.grpc import auth_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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
    docs_url="/api/college/docs" if settings.DEBUG else None,
    redoc_url="/api/college/redoc" if settings.DEBUG else None,
    openapi_url="/api/college/openapi.json" if settings.DEBUG else None,
)

app.include_router(health_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(college_router, prefix="/api")
