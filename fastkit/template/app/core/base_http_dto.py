from abc import abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

from app.core.base_entity import BaseEntity

TEntity = TypeVar("TEntity", bound=BaseEntity)


class BaseResponseDto(BaseModel, Generic[TEntity]):
    @abstractmethod
    def to_entity(self) -> TEntity:
        raise NotImplementedError
