"""Storage interface for authorization decisions."""

from abc import ABC, abstractmethod
from uuid import UUID


class AccessRepository(ABC):
    @abstractmethod
    async def list_role_grants(self) -> set[tuple[UUID, str, str]]:
        """Load active role ID, resource, and action grants for the cache."""

    @abstractmethod
    async def list_user_role_ids(self, user_id: UUID) -> set[UUID]:
        """Load the user's current role assignments."""
