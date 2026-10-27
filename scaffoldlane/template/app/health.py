from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
