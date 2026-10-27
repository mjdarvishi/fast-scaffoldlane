import json
from typing import Any
from fastapi.encoders import jsonable_encoder
from app.core.dependency import injectable
from app.core.redis.connection import MainRedisConnection

@injectable(singleton=True)
class RedisKVService:
    expire_default = 900

    def __init__(self, conn: MainRedisConnection):
        self._redis = conn.redis

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

    async def set(self, key: str, value: Any=None, expire: int | None=None):
        if value is None:
            value = {}
        await self._redis.set(key, self._encode(value), ex=expire)

    async def get(self, key: str) -> Any:
        value = await self._redis.get(key)
        return self._decode(value)

    async def delete(self, key: str):
        await self._redis.delete(key)

    async def set_with_shadow(self, key: str, value: Any=None, expire: int=70, shadow_prefix: str='SH_'):
        if value is None:
            value = {}
        await self.set(key, value)
        await self._redis.set(f'{shadow_prefix}{key}', '', ex=expire)

    async def hset(self, key: str, mapping: dict[str, Any], expire: int | None=None):
        if not mapping:
            return
        encoded = {k: self._encode(v) for k, v in mapping.items()}
        await self._redis.hset(name=key, mapping=encoded)
        if expire:
            await self._redis.expire(key, expire)

    async def hget(self, key: str, field: str) -> Any:
        value = await self._redis.hget(key, field)
        return self._decode(value)

    async def hincrby(self, key: str, field: str, amount: int=1):
        new_value = await self._redis.hincrby(key, field, amount)
        return new_value

    async def hgetall(self, key: str) -> dict[str, Any]:
        raw = await self._redis.hgetall(key)
        result = {}
        for k, v in raw.items():
            field = k.decode() if isinstance(k, bytes) else k
            decoded = self._decode(v)
            if decoded is not None:
                result[field] = decoded
        return result

    async def hmget(self, key: str, fields: list[str]) -> dict[str, Any]:
        values = await self._redis.hmget(key, fields)
        result = {}
        for f, v in zip(fields, values, strict=False):
            decoded = self._decode(v)
            if decoded is not None:
                result[f] = decoded
        return result

    async def hdel(self, key: str, field: str):
        await self._redis.hdel(key, field)

    async def keys(self, prefix: str) -> list[str]:
        keys = await self._redis.keys(f'{prefix}*')
        return [k.decode() if isinstance(k, bytes) else k for k in keys]

    async def add_to_set(self, key: str, value: str):
        await self._redis.sadd(key, value)

    async def remove_from_set(self, key: str, value: str):
        await self._redis.srem(key, value)

    async def get_set_members(self, key: str) -> list[str]:
        """Return all members of a Redis set"""
        members = await self._redis.smembers(key)
        return [m.decode() if isinstance(m, bytes) else m for m in members]
