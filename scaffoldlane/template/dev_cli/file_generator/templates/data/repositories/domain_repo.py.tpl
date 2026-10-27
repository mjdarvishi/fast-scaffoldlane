from uuid import UUID

from app.core.dependency import provides
from app.features.{domain}.domain.entities import {domain_class}Entity
from app.features.{domain}.domain.repositories import {domain_class}Repository


@provides({domain_class}Repository)
class {domain_class}RepositoryImpl({domain_class}Repository):
    async def get_by_id(self, id: UUID) -> {domain_class}Entity | None:
        # Implement storage access and map rows directly to the domain entity.
        raise NotImplementedError
