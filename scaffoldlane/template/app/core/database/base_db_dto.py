from abc import abstractmethod
from typing import Generic, TypeVar

from app.core.base_entity import BaseEntity
from app.core.model.models import Base

TEntity = TypeVar("TEntity", bound=BaseEntity)


class BaseDBDto(Base, Generic[TEntity]):
    __abstract__ = True

    @abstractmethod
    def to_entity(self) -> TEntity:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def from_entity(entity: TEntity) -> "BaseDBDto":
        raise NotImplementedError
