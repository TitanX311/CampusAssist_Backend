from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/college/health", summary="Health check")
async def health() -> dict:
    return {"status": "ok"}
