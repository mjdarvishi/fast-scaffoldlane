from contextvars import ContextVar
from sqlalchemy.ext.asyncio import AsyncSession

session_var: ContextVar[AsyncSession] = ContextVar("session_var")
# Depth of nested TransactionManager.transaction() blocks in the current context; 0 means no active transaction.
in_transaction_var: ContextVar[int] = ContextVar("in_transaction", default=0)

# Shared request correlation context for structured logs.
trace_id_var: ContextVar[str] = ContextVar("request_trace_id", default="")
span_id_var: ContextVar[str] = ContextVar("request_span_id", default="")
