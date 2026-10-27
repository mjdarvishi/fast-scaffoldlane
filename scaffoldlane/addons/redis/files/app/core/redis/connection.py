import asyncio
from contextlib import suppress

import redis.asyncio as redis

from app.core.config import Settings
from app.core.dependency import injectable
from app.core.logging.logging_service import LoggingService


class BaseRedisConnection:
    def __init__(self, host: str, port: int, logger: LoggingService, db: int = 0,
                 reconnect_delay_seconds: int = 5, password: str | None = None):
        self._pool = redis.ConnectionPool(host=host, port=port, db=db, password=password,
                                          decode_responses=True)
        self.redis = redis.Redis(connection_pool=self._pool)
        self._logger = logger
        self._is_connected = False
        self._started = False
        self._reconnect_delay_seconds = reconnect_delay_seconds
        self._connection_task: asyncio.Task[None] | None = None

    async def connect(self) -> None:
        if self._started:
            return
        self._started = True
        self._connection_task = asyncio.create_task(self._connect_forever())

    async def _connect_forever(self) -> None:
        while self._started:
            try:
                await self.redis.ping()
                if not self._is_connected:
                    self._logger.info("Redis connected successfully")
                self._is_connected = True
            except asyncio.CancelledError:
                raise
            except redis.RedisError as exc:
                self._is_connected = False
                self._logger.error(f"Redis connection error: {exc}")
            await asyncio.sleep(self._reconnect_delay_seconds)

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    async def close(self) -> None:
        self._started = False
        if self._connection_task:
            self._connection_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._connection_task
        self._connection_task = None
        await self.redis.aclose()
        await self._pool.aclose()
        self._is_connected = False


@injectable(singleton=True)
class MainRedisConnection(BaseRedisConnection):
    def __init__(self, settings: Settings, logger: LoggingService):
        super().__init__(host=settings.redis.host, port=settings.redis.port,
                         db=settings.redis.db, password=settings.redis.password,
                         logger=logger,
                         reconnect_delay_seconds=settings.redis.reconnect_delay_seconds)
