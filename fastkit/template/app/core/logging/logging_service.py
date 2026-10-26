import logging
from typing import Any

from fastapi import Request

from app.core.dependency import injectable
from app.core.logging.logging_config import LogConfig


class BaseLoggingService:
    """Shared structured logging behavior for API and worker services."""

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    @staticmethod
    def _request_context(request: Request) -> dict[str, Any]:
        return {
            "method": request.method,
            "path": request.url.path,
            "query": dict(request.query_params),
            "client_ip": request.client.host if request.client else "unknown",
        }

    def info(self, message: str) -> None:
        self._logger.info(message)

    def debug(self, message: str) -> None:
        self._logger.debug(message)

    def warning(self, message: str) -> None:
        self._logger.warning(message)

    def error(self, message: str, exc_info: bool = False) -> None:
        self._logger.error(message, exc_info=exc_info)

    def request_succeeded(self, request: Request, status_code: int, duration_ms: int) -> None:
        is_slow = duration_ms > 1000
        request_log = {
            "event": "request",
            **self._request_context(request),
            "status_code": status_code,
            "duration_ms": duration_ms,
            "is_slow": is_slow,
        }

        self._logger.log(
            level=logging.WARNING if is_slow else logging.INFO,
            msg="request",
            extra={"event_data": request_log},
        )

    def request_failed(self, request: Request, duration_ms: int, error: Exception) -> None:
        self._logger.error(
            "request_failed",
            extra={
                "event_data": {
                    "event": "request_failed",
                    **self._request_context(request),
                    "duration_ms": duration_ms,
                    "error": str(error),
                }
            },
            exc_info=True,
        )


@injectable(singleton=True)
class LoggingService(BaseLoggingService):
    """API logging service."""

    def __init__(self):
        super().__init__(LogConfig.get_app_logger())


@injectable(singleton=True)
class WorkerLoggingService(BaseLoggingService):
    """Worker logging service."""

    def __init__(self):
        super().__init__(LogConfig.get_worker_logger())
