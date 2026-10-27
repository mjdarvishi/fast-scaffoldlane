from contextlib import asynccontextmanager

from app.core.context_var import in_transaction_var, session_var


class TransactionManager:
    @classmethod
    def is_in_transaction(cls) -> bool:
        """Check if a transaction is currently active."""
        return in_transaction_var.get() > 0

    @classmethod
    @asynccontextmanager
    async def transaction(cls):
        """Run repository calls atomically on the current context's session.

        Reentrant: a nested call joins the outer transaction (only the outermost
        scope commits or rolls back), so use cases can call other use cases/repos
        that also open a transaction without prematurely committing.
        """
        depth = in_transaction_var.get()
        in_transaction_var.set(depth + 1)
        try:
            yield
        except Exception:
            if depth == 0:
                await session_var.get().rollback()
            raise
        else:
            if depth == 0:
                await session_var.get().commit()
        finally:
            in_transaction_var.set(depth)
