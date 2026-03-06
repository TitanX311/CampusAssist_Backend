from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Health"])


@router.get("/search/health", summary="Health check")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "search-service"})
