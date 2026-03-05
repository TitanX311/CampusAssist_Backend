from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get("/community/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": "community_service",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
