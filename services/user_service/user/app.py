from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from user.config.database import engine
from user.config.settings import get_settings
from user.grpc import auth_client
from user.models import Base
from user.routes.health import router as health_router
from user.routes.user import router as user_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables (use Alembic migrations in production).
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await auth_client.close()
    await engine.dispose()


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=settings.APP_NAME,
        version="1.0.0",
        description=(
            "User Service for Campus Assist — returns user profiles with "
            "aggregated activity stats (posts, comments, communities)."
        ),
        contact={"name": "Campus Assist", "url": "https://github.com/campus-assist"},
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    app.openapi_schema = schema
    return app.openapi_schema


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    docs_url="/api/users/docs" if settings.DEBUG else None,
    redoc_url="/api/users/redoc" if settings.DEBUG else None,
    openapi_url="/api/users/openapi.json" if settings.DEBUG else None,
)

app.openapi = custom_openapi

app.include_router(health_router)
app.include_router(user_router)
