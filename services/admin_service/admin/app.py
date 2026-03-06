"""
Admin Service — internal admin panel for Campus Assist.

Single FastAPI application that:
  • Verifies every request is SUPER_ADMIN (live gRPC call to auth_service)
  • Proxies read/write/delete operations to all backend services
  • Provides aggregate health + stats endpoints for monitoring

No database — pure aggregation + proxy layer.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from admin.config.settings import get_settings
from admin.grpc import auth_client
from admin.routes.attachments import router as attachments_router
from admin.routes.colleges import router as colleges_router
from admin.routes.comments import router as comments_router
from admin.routes.communities import router as communities_router
from admin.routes.health import router as health_router
from admin.routes.posts import router as posts_router
from admin.routes.stats import router as stats_router
from admin.routes.users import router as users_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Graceful shutdown: close the auth gRPC channel
    await auth_client.close()


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=settings.APP_NAME,
        version="1.0.0",
        description=(
            "**Campus Assist — Internal Admin Panel**\n\n"
            "Unified API for debugging, managing, monitoring, and surveillance "
            "of all Campus Assist microservices.\n\n"
            "All endpoints except `/api/admin/health` require a valid "
            "`Authorization: Bearer <token>` where the token belongs to a **SUPER_ADMIN** user.\n\n"
            "Role is verified **live** via gRPC to `auth_service` on every request — "
            "no JWT role claim is trusted."
        ),
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
    docs_url="/api/admin/docs" if settings.DEBUG else None,
    redoc_url="/api/admin/redoc" if settings.DEBUG else None,
    openapi_url="/api/admin/openapi.json" if settings.DEBUG else None,
)

app.openapi = custom_openapi

# Route registration order matters — more-specific prefixes first
app.include_router(health_router,      prefix="/api")
app.include_router(stats_router,       prefix="/api")
app.include_router(users_router,       prefix="/api")
app.include_router(communities_router, prefix="/api")
app.include_router(posts_router,       prefix="/api")
app.include_router(comments_router,    prefix="/api")
app.include_router(colleges_router,    prefix="/api")
app.include_router(attachments_router, prefix="/api")
