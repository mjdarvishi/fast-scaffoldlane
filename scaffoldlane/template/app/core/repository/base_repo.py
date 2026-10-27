from math import ceil
from typing import TypeVar, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context_var import session_var
from app.core.database import TransactionManager
from app.core.exception.base_exception import DataBaseException

T = TypeVar("T")


class BaseRepository:
    @property
    def session(self) -> AsyncSession:
        return session_var.get()

    async def execute(self, stmt):
        try:
            result = await self.session.execute(stmt)
            await self.commit()
            return result
        except Exception as exc:
            await self.session.rollback()
            raise DataBaseException(exc=exc, message=None) from exc

    async def commit(self):
        try:
            if TransactionManager.is_in_transaction():
                await self.session.flush()
            else:
                await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            raise DataBaseException(exc=exc) from exc

    async def save(self, model):
        try:
            self.session.add(model)
            await self.commit()
        except Exception as exc:
            await self.session.rollback()
            raise DataBaseException(exc=exc) from exc

    async def save_all(self, models):
        try:
            self.session.add_all(list(models))
            await self.commit()
        except Exception as exc:
            await self.session.rollback()
            raise DataBaseException(exc=exc) from exc

    async def pagination(self, stmt, page: int, limit: int) -> tuple[T, int, int]:
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.execute(count_stmt)
        total_count = count_result.scalar_one()
        total_pages = ceil(total_count / limit) if total_count > 0 else 1
        page_result = await self.execute(stmt.offset((page - 1) * limit).limit(limit))
        result: T = cast(T, page_result.scalars().unique().all())
        return result, total_pages, total_count
