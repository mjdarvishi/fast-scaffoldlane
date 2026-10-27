import json
from contextlib import contextmanager
from typing import Any

from fastapi.encoders import jsonable_encoder
from opentelemetry.trace import Status, StatusCode

from app.core.dependency import injectable
from app.core.redis.connection import MainRedisConnection
from app.core.tracing import tracer


@contextmanager
def _redis_span(operation: str, key: str, **attributes: Any):
    with tracer.start_as_current_span(f"redis.{operation.lower()}") as span:
        span.set_attribute("db.system", "redis")
        span.set_attribute("db.operation", operation.upper())
        span.set_attribute("redis.key", key)
        for name, value in attributes.items():
            if value is not None:
                span.set_attribute(name, value)
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


@injectable(singleton=True)
class RedisKVService:
    expire_default = 900  # 15 minutes

    def __init__(self, conn: MainRedisConnection):
        self._redis = conn.redis

    # -----------------------
    # Serialization helpers
    # -----------------------
    @staticmethod
    def _encode(value: Any) -> str:
        return json.dumps(jsonable_encoder(value))

    @staticmethod
    def _decode(value: Any) -> Any:
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None

    # -----------------------
    # Basic KV
    # -----------------------
    async def set(self, key: str, value: Any = None, expire: int | None = None):
        if value is None:
            value = {}
        with _redis_span("set", key, **{"redis.expire_seconds": expire}):
            await self._redis.set(key, self._encode(value), ex=expire)

    async def get(self, key: str) -> Any:
        with _redis_span("get", key) as span:
            value = await self._redis.get(key)
            span.set_attribute("redis.hit", value is not None)
            return self._decode(value)

    async def delete(self, key: str):
        with _redis_span("delete", key):
            await self._redis.delete(key)

    # -----------------------
    # Shadow key pattern
    # -----------------------
    async def set_with_shadow(
        self,
        key: str,
        value: Any = None,
        expire: int = 70,
        shadow_prefix: str = "SH_",
    ):
        with _redis_span(
            "set_with_shadow",
            key,
            **{"redis.shadow_key": f"{shadow_prefix}{key}", "redis.expire_seconds": expire},
        ):
            if value is None:
                value = {}
            await self.set(key, value)
            await self._redis.set(f"{shadow_prefix}{key}", "", ex=expire)

    # -----------------------
    # Hash operations
    # -----------------------
    async def hset(
        self,
        key: str,
        mapping: dict[str, Any],
        expire: int | None = None,
    ):
        if not mapping:
            return

        with _redis_span(
            "hset",
            key,
            **{"redis.field_count": len(mapping), "redis.expire_seconds": expire},
        ):
            encoded = {k: self._encode(v) for k, v in mapping.items()}
            await self._redis.hset(name=key, mapping=encoded)

            if expire:
                await self._redis.expire(key, expire)

    async def hget(self, key: str, field: str) -> Any:
        with _redis_span("hget", key, **{"redis.field": field}) as span:
            value = await self._redis.hget(key, field)
            span.set_attribute("redis.hit", value is not None)
            return self._decode(value)

    async def hincrby(self, key: str, field: str, amount: int = 1):
        with _redis_span("hincrby", key, **{"redis.field": field, "redis.amount": amount}):
            new_value = await self._redis.hincrby(key, field, amount)
            return new_value

    async def hgetall(self, key: str) -> dict[str, Any]:
        with _redis_span("hgetall", key) as span:
            raw = await self._redis.hgetall(key)
            span.set_attribute("redis.field_count", len(raw))

            result = {}
            for k, v in raw.items():
                field = k.decode() if isinstance(k, bytes) else k
                decoded = self._decode(v)
                if decoded is not None:
                    result[field] = decoded

            return result

    async def hmget(self, key: str, fields: list[str]) -> dict[str, Any]:
        with _redis_span("hmget", key, **{"redis.field_count": len(fields)}) as span:
            values = await self._redis.hmget(key, fields)

            result = {}
            for f, v in zip(fields, values, strict=False):
                decoded = self._decode(v)
                if decoded is not None:
                    result[f] = decoded

            span.set_attribute("redis.hit_count", len(result))
            return result

    async def hdel(self, key: str, field: str):
        with _redis_span("hdel", key, **{"redis.field": field}):
            await self._redis.hdel(key, field)

    async def keys(self, prefix: str) -> list[str]:
        with _redis_span("keys", f"{prefix}*", **{"redis.key_prefix": prefix}) as span:
            keys = await self._redis.keys(f"{prefix}*")
            span.set_attribute("redis.result_count", len(keys))
            return [k.decode() if isinstance(k, bytes) else k for k in keys]

    # -----------------------
    # Set operations for online SIDs
    # -----------------------
    async def add_to_set(self, key: str, value: str):
        with _redis_span("sadd", key):
            await self._redis.sadd(key, value)

    async def remove_from_set(self, key: str, value: str):
        with _redis_span("srem", key):
            await self._redis.srem(key, value)

    async def get_set_members(self, key: str) -> list[str]:
        """Return all members of a Redis set"""
        with _redis_span("smembers", key) as span:
            members = await self._redis.smembers(key)
            span.set_attribute("redis.member_count", len(members))
            return [m.decode() if isinstance(m, bytes) else m for m in members]


