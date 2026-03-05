from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


@router.get(
    "/community/health",
    response_model=HealthResponse,
    summary="Service health check",
    description=(
        "Returns the current liveness status of the community service.\n\n"
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
                        "service": "community_service",
                        "version": "1.0.0",
                        "timestamp": "2026-03-06T12:00:00+00:00",
                    }
                }
            },
        }
    },
)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="community_service",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
