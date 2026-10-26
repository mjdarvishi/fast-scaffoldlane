"""SQLAlchemy async database module for PostgreSQL."""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import Settings
from app.core.dependency import injector
from app.core.database.sqlalchemy_metrics import register_sqlalchemy_metrics


__SETTINGS: Settings = injector.get(Settings)

__SQLALCHEMY_DATABASE_URL = (
    f"postgresql+asyncpg://{__SETTINGS.database.user}:{__SETTINGS.database.password}"
    f"@{__SETTINGS.database.host}:{__SETTINGS.database.port}/{__SETTINGS.database.name}"
)

engine = create_async_engine(
    __SQLALCHEMY_DATABASE_URL,
    future=True,
    pool_size=10,
    max_overflow=5,
    pool_recycle=3600,
    echo=False,
)

register_sqlalchemy_metrics(engine)

# Shared SQLAlchemy session factory.
session_factory = async_sessionmaker(
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


# Register SQLAlchemy session factory and AsyncSession provider in the injector.
injector.register(async_sessionmaker, lambda: session_factory)
injector.register(AsyncSession, lambda: injector.get(async_sessionmaker)())
