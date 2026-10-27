from abc import ABC, abstractmethod
from uuid import UUID

from app.features.{domain}.domain.entities import {domain_class}Entity


class {domain_class}Repository(ABC):
    @abstractmethod
    async def get_by_id(self, id: UUID) -> {domain_class}Entity | None:
        """Return an entity by ID, or None when absent."""
