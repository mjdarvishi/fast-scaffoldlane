from fastapi import APIRouter

from app.api.versions import ApiVersion
from app.health import router as health_router

router = APIRouter(prefix=ApiVersion.V1.prefix)
router.include_router(health_router)

# Register feature routers here as the project grows.
