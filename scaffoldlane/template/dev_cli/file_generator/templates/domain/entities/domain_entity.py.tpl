from dataclasses import dataclass
from uuid import UUID

from app.core.base_entity import BaseEntity


@dataclass
class {domain_class}Entity(BaseEntity):
    id: UUID
