from typing import TYPE_CHECKING

from app.core.database.base_db_dto  import BaseDBDto

if TYPE_CHECKING:
    from app.features.{domain}.domain.entities.{domain} import {domain_class}Entity


class {domain_class}Dto(BaseDBDto["{domain_class}Entity"]):
    __abstract__ = True
    pass
