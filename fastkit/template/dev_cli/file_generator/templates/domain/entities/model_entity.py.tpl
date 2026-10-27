from dataclasses import dataclass
from uuid import UUID

from app.core.base_entity import BaseEntity


@dataclass
class {model_class}Entity(BaseEntity):
    id: UUID
