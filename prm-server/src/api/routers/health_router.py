from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health/live", summary="Liveness probe")
async def liveness() -> dict:  # type: ignore[type-arg]
    return {"status": "ok"}
