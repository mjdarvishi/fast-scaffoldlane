from typing import TYPE_CHECKING

from app.core.database.base_db_dto  import BaseDBDto

if TYPE_CHECKING:
    from app.features.{domain}.domain.entities.{model} import {model_class}Entity


class {model_class}Dto(BaseDBDto["{model_class}Entity"]):
    __abstract__ = True
    pass
