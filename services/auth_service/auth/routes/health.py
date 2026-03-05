from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth.config.settings import Settings, get_settings

router = APIRouter(prefix="/auth/health", tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    debug: bool
    timestamp: str


@router.get(
    "",
    response_model=HealthResponse,
    summary="Service health check",
    description=(
        "Returns the current liveness status of the auth service.\n\n"
        "Used by Kubernetes readiness/liveness probes and uptime monitors. "
        "A `200 OK` with `status: ok` means the service is running and reachable."
    ),
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "service": "auth_service",
                        "version": "1.0.0",
                        "debug": False,
                        "timestamp": "2026-03-06T12:00:00+00:00",
                    }
                }
            },
        }
    },
)
def health_check(settings: Settings = Depends(get_settings)):
    """Returns the current health status of the auth service."""
    return HealthResponse(
        status="ok",
        service=settings.APP_NAME,
        version="1.0.0",
        debug=settings.DEBUG,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
