from fastapi import APIRouter

from app.api.versions import ApiVersion
from app.health import router as health_router
from app.features.auth import AuthDomain

router = APIRouter(prefix=ApiVersion.V1.prefix)
router.include_router(health_router)
router.include_router(AuthDomain.router)

# Register feature routers here as the project grows.
