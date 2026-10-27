"""PostgreSQL adapter for local user identities."""

from sqlalchemy import text

from app.core.database.database import session_factory
from app.core.dependency import provides
from app.features.auth.domain.entities import UserAccountEntity, UserCredentialsEntity
from app.features.auth.domain.repositories import UserRepository


@provides(UserRepository)
class UserRepositoryImpl(UserRepository):
    async def create(self, *, email: str, password_hash: str) -> UserAccountEntity | None:
        async with session_factory() as session:
            result = await session.execute(text("""
                INSERT INTO users (email, password_hash)
                VALUES (:email, :password_hash)
                ON CONFLICT (email) DO NOTHING
                RETURNING id, email
            """).bindparams(email=email, password_hash=password_hash))
            row = result.mappings().one_or_none()
            await session.commit()
            return UserAccountEntity(**row) if row else None

    async def get_credentials(self, *, email: str) -> UserCredentialsEntity | None:
        async with session_factory() as session:
            result = await session.execute(text("""
                SELECT id, email, password_hash, is_active FROM users WHERE email = :email
            """).bindparams(email=email))
            row = result.mappings().one_or_none()
            return UserCredentialsEntity(**row) if row else None
