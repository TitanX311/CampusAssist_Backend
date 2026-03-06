"""
Aggregate health check — pings every backend service and reports status + latency.
Does NOT require super-admin auth so it can be used for monitoring probes.
"""
import asyncio
import time
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

from admin.config.settings import get_settings

router = APIRouter(prefix="/admin/health", tags=["Admin Health"])


class ServiceHealth(BaseModel):
    status: str          # "ok" | "degraded" | "unreachable"
    latency_ms: float | None = None
    status_code: int | None = None


class HealthResponse(BaseModel):
    status: str          # "ok" if all services healthy, else "degraded"
    service: str
    version: str
    timestamp: str
    services: dict[str, ServiceHealth]


async def _ping(name: str, url: str) -> tuple[str, ServiceHealth]:
    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(url)
        latency = round((time.monotonic() - t0) * 1000, 1)
        ok = r.status_code == 200
        return name, ServiceHealth(
            status="ok" if ok else "degraded",
            latency_ms=latency,
            status_code=r.status_code,
        )
    except Exception:
        return name, ServiceHealth(status="unreachable")


@router.get(
    "",
    response_model=HealthResponse,
    summary="Aggregate health check",
    description=(
        "Pings the health endpoint of every backend service in parallel and "
        "returns a summary. Status is `ok` only when all services respond 200."
    ),
)
async def aggregate_health() -> HealthResponse:
    settings = get_settings()
    targets = {
        "auth_service":       f"{settings.AUTH_SERVICE_URL}/api/auth/health",
        "community_service":  f"{settings.COMMUNITY_SERVICE_URL}/api/community/health",
        "post_service":       f"{settings.POST_SERVICE_URL}/api/posts/health",
        "comment_service":    f"{settings.COMMENT_SERVICE_URL}/api/comments/health",
        "attachment_service": f"{settings.ATTACHMENT_SERVICE_URL}/api/attachments/health",
        "college_service":    f"{settings.COLLEGE_SERVICE_URL}/api/college/health",
    }

    results = dict(await asyncio.gather(*[_ping(n, u) for n, u in targets.items()]))
    overall = "ok" if all(s.status == "ok" for s in results.values()) else "degraded"

    return HealthResponse(
        status=overall,
        service=settings.APP_NAME,
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        services=results,
    )
