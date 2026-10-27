"""PostgreSQL implementation of the access repository."""

from uuid import UUID

from sqlalchemy import text

from app.core.database.database import session_factory
from app.core.dependency import provides
from app.core.authorization.repository import AccessRepository


@provides(AccessRepository)
class SqlAccessRepository(AccessRepository):
    async def list_role_grants(self) -> set[tuple[UUID, str, str]]:
        async with session_factory() as session:
            result = await session.execute(text("""
                SELECT r.id, p.resource, p.action
                FROM roles AS r
                JOIN role_permission_grants AS g ON g.role_id = r.id
                JOIN permissions AS p ON p.id = g.permission_id
                WHERE r.is_active = TRUE
            """))
            return {(row.id, row.resource, row.action) for row in result}

    async def list_user_role_ids(self, user_id: UUID) -> set[UUID]:
        async with session_factory() as session:
            result = await session.execute(text("""
                SELECT role_id FROM user_roles WHERE user_id = :user_id
            """).bindparams(user_id=user_id))
            return set(result.scalars())
