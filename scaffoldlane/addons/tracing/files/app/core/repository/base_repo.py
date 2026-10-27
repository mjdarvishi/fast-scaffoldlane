from math import ceil
from typing import TypeVar, cast

from opentelemetry.trace import Status, StatusCode
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context_var import session_var
from app.core.database import TransactionManager
from app.core.exception.base_exception import (
    DataBaseException,
)
from app.core.tracing import tracer

T = TypeVar("T")


def _db_operation_from_statement(stmt) -> str:
    statement_type = stmt.__class__.__name__.lower()
    if "select" in statement_type:
        return "SELECT"
    if "insert" in statement_type:
        return "INSERT"
    if "update" in statement_type:
        return "UPDATE"
    if "delete" in statement_type:
        return "DELETE"
    return statement_type.upper()


def _model_name(model) -> str:
    return model.__class__.__name__


class BaseRepository:
    @property
    def session(self) -> AsyncSession:
        session = session_var.get()
        return session

    async def execute(self, stmt):
        operation = _db_operation_from_statement(stmt)
        with tracer.start_as_current_span(f"db.{operation.lower()}") as span:
            span.set_attribute("db.system", "postgresql")
            span.set_attribute("db.operation", operation)
            span.set_attribute("db.statement_type", stmt.__class__.__name__)
            span.set_attribute("repository.name", self.__class__.__name__)
            span.set_attribute("db.transaction.active", TransactionManager.is_in_transaction())
            try:
                result = await self.session.execute(stmt)
                await self.commit()
                return result
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                await self.session.rollback()
                raise DataBaseException(exc=e, message=None) from e

    async def commit(self):
        operation = "flush" if TransactionManager.is_in_transaction() else "commit"
        with tracer.start_as_current_span(f"db.{operation}") as span:
            span.set_attribute("db.system", "postgresql")
            span.set_attribute("db.operation", operation.upper())
            span.set_attribute("repository.name", self.__class__.__name__)
            span.set_attribute("db.transaction.active", TransactionManager.is_in_transaction())
            try:
                if TransactionManager.is_in_transaction():
                    await self.session.flush()
                else:
                    await self.session.commit()
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                await self.session.rollback()
                raise DataBaseException(exc=e) from e

    async def save(self, model):
        with tracer.start_as_current_span(f"db.save.{_model_name(model)}") as span:
            span.set_attribute("db.system", "postgresql")
            span.set_attribute("db.operation", "SAVE")
            span.set_attribute("db.model", _model_name(model))
            span.set_attribute("repository.name", self.__class__.__name__)
            span.set_attribute("db.transaction.active", TransactionManager.is_in_transaction())
            try:
                self.session.add(model)
                if TransactionManager.is_in_transaction():
                    await self.session.flush()
                else:
                    await self.session.commit()
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                await self.session.rollback()
                raise DataBaseException(exc=e) from e

    async def save_all(self, models):
        models = list(models)
        model_name = _model_name(models[0]) if models else "unknown"
        with tracer.start_as_current_span(f"db.save_all.{model_name}") as span:
            span.set_attribute("db.system", "postgresql")
            span.set_attribute("db.operation", "SAVE_ALL")
            span.set_attribute("db.model", model_name)
            span.set_attribute("db.rows", len(models))
            span.set_attribute("repository.name", self.__class__.__name__)
            span.set_attribute("db.transaction.active", TransactionManager.is_in_transaction())
            try:
                self.session.add_all(models)
                if TransactionManager.is_in_transaction():
                    await self.session.flush()
                else:
                    await self.session.commit()
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                await self.session.rollback()
                raise DataBaseException(exc=e) from e

    async def pagination(self, stmt, page: int, limit: int) -> tuple[T, int, int]:
        with tracer.start_as_current_span("db.pagination") as span:
            span.set_attribute("db.system", "postgresql")
            span.set_attribute("db.operation", "PAGINATION")
            span.set_attribute("db.statement_type", stmt.__class__.__name__)
            span.set_attribute("repository.name", self.__class__.__name__)
            span.set_attribute("db.transaction.active", TransactionManager.is_in_transaction())
            span.set_attribute("db.pagination.page", page)
            span.set_attribute("db.pagination.limit", limit)
            try:
                count_stmt = select(func.count()).select_from(stmt.subquery())
                count_result = await self.execute(count_stmt)
                total_count = count_result.scalar_one()
                total_pages = ceil(total_count / limit) if total_count > 0 else 1
                page_result = await self.execute(stmt.offset((page - 1) * limit).limit(limit))
                result: T = cast(T, page_result.scalars().unique().all())
                span.set_attribute("db.pagination.total_count", total_count)
                span.set_attribute("db.pagination.total_pages", total_pages)
                span.set_attribute("db.pagination.result_count", len(result))
                return result, total_pages, total_count
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
