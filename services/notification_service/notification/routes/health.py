from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/notifications/health",
    include_in_schema=False,
)
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})
