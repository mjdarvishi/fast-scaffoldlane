from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.core.base_entity import BaseEntity


@dataclass
class {model_class}Entity(BaseEntity):
    id: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    pass
