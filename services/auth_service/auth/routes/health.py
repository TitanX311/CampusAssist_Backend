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


@router.get("", response_model=HealthResponse, summary="Health check")
def health_check(settings: Settings = Depends(get_settings)):
    """Returns the current health status of the auth service."""
    return HealthResponse(
        status="ok",
        service=settings.APP_NAME,
        version="1.0.0",
        debug=settings.DEBUG,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
