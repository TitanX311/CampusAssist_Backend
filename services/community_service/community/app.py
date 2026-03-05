from contextlib import asynccontextmanager

from fastapi import FastAPI

from community.config.database import engine
from community.config.settings import get_settings
from community.models.base import Base
from community.routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
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
