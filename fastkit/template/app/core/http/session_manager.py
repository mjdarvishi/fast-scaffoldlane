from typing import Any

import httpx

from app.core.config import Settings
from app.core.dependency import injectable


@injectable(singleton=True)
class HTTPSessionManager:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            timeout = httpx.Timeout(float(self._settings.app.call_timeout))
            self._client = httpx.AsyncClient(timeout=timeout)
        return self._client

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        return await self.client.request(method=method, url=url, **kwargs)

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
