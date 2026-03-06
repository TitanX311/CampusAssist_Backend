from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from sqlalchemy import text

from auth.config.database import engine
from auth.config.settings import get_settings
from auth.models import Base  # ensures all models are registered
from auth.routes.auth import router as auth_router
from auth.routes.admin import router as admin_router
from auth.routes.health import router as health_router
from auth.grpc import server as grpc_server

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup (use Alembic migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Ensure SUPER_ADMIN is present in the PostgreSQL user_type enum
        await conn.execute(
            text("ALTER TYPE user_type ADD VALUE IF NOT EXISTS 'SUPER_ADMIN'")
        )
    _settings = get_settings()
    await grpc_server.serve(_settings.GRPC_PORT)
    yield
    await grpc_server.stop()
    await engine.dispose()


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=settings.APP_NAME,
        version="1.0.0",
        description="Authentication service for Campus Assist — Google OAuth sign-in, JWT session management.",
        contact={
            "name": "Campus Assist",
            "url": "https://github.com/campus-assist",
        },
        routes=app.routes,
    )

    # Add Bearer token security scheme
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
    docs_url="/api/auth/docs" if settings.DEBUG else None,
    redoc_url="/api/auth/redoc" if settings.DEBUG else None,
    openapi_url="/api/auth/openapi.json" if settings.DEBUG else None,
)

app.openapi = custom_openapi

app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(admin_router, prefix="/api")