"""FastAPI dependency factory for protected routes."""

from collections.abc import Callable
from uuid import UUID

from fastapi import Depends

from app.core.auth.dependency import get_current_user_id
from app.core.authorization.access_manager import AccessManager
from app.core.dependency import injector


def require_permission(resource: str, action: str) -> Callable:
    async def check(user_id: UUID = Depends(get_current_user_id)) -> None:
        await injector.get(AccessManager).require(
            user_id=user_id, resource=resource, action=action
        )

    return check
