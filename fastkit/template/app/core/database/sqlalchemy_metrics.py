"""SQLAlchemy event hooks for Prometheus database metrics."""

from __future__ import annotations

import re
import time
import weakref

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.prometheus_metrics import (
    database_errors_total,
    database_queries_total,
    database_query_duration_seconds,
)


_TABLE_PATTERN = re.compile(
    r"(?:from|into|update|join|table)\s+[`\"]?([a-zA-Z_][a-zA-Z0-9_]*)",
    flags=re.IGNORECASE,
)

_REGISTERED_ENGINES: "weakref.WeakSet[Engine]" = weakref.WeakSet()


def _extract_operation_and_table(statement: str) -> tuple[str, str]:
    normalized = (statement or "").strip()
    if not normalized:
        return ("UNKNOWN", "unknown")

    operation = normalized.split(maxsplit=1)[0].upper()
    match = _TABLE_PATTERN.search(normalized)
    table = match.group(1).lower() if match else "unknown"
    return (operation, table)


def register_sqlalchemy_metrics(async_engine: AsyncEngine) -> None:
    """Attach SQLAlchemy listeners to collect DB query metrics."""
    sync_engine: Engine = async_engine.sync_engine
    if sync_engine in _REGISTERED_ENGINES:
        return

    @event.listens_for(sync_engine, "before_cursor_execute")
    def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault("query_start_times", []).append(time.perf_counter())

    @event.listens_for(sync_engine, "after_cursor_execute")
    def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        start_times = conn.info.get("query_start_times") or []
        started_at = start_times.pop() if start_times else time.perf_counter()
        duration = max(0.0, time.perf_counter() - started_at)

        operation, table = _extract_operation_and_table(statement)
        database_queries_total.labels(operation=operation, table=table).inc()
        database_query_duration_seconds.labels(operation=operation, table=table).observe(duration)

    @event.listens_for(sync_engine, "handle_error")
    def _handle_error(exception_context):
        statement = exception_context.statement or ""
        operation, table = _extract_operation_and_table(statement)
        error_type = type(exception_context.original_exception).__name__
        database_errors_total.labels(
            operation=operation,
            table=table,
            error_type=error_type,
        ).inc()

    _REGISTERED_ENGINES.add(sync_engine)
