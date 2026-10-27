"""Application-facing authorization service with cached role grants."""

import asyncio
from uuid import UUID

from app.core.dependency import injectable
from app.core.exception.base_exception import AccessDeniyedException
from app.core.authorization.repository import AccessRepository


@injectable(singleton=True)
class AccessManager:
    def __init__(self, repository: AccessRepository) -> None:
        self._repository = repository
        self._grants: frozenset[tuple[UUID, str, str]] | None = None
        self._grants_lock = asyncio.Lock()

    async def _role_grants(self) -> frozenset[tuple[UUID, str, str]]:
        if self._grants is None:
            async with self._grants_lock:
                if self._grants is None:
                    self._grants = frozenset(await self._repository.list_role_grants())
        return self._grants

    async def invalidate_grants(self) -> None:
        """Call after changing roles, permissions, or role grants."""
        async with self._grants_lock:
            self._grants = None

    async def require(self, *, user_id: UUID, resource: str, action: str) -> None:
        grants = await self._role_grants()
        role_ids = await self._repository.list_user_role_ids(user_id)
        if not any((role_id, resource, action) in grants for role_id in role_ids):
            raise AccessDeniyedException(message=f"Permission denied: {resource}:{action}")
