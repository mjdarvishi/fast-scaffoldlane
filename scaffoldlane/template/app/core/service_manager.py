import logging
from dataclasses import dataclass

from fastapi import FastAPI

from app.core.config import Settings
from app.core.dependency import injector
from app.core.logging.logging_config import LogConfig


@dataclass(frozen=True)
class ServiceContext:
    settings: Settings
    logger: logging.Logger


class ServiceManager:
    def __init__(
        self,
        logger_name: str,
        log_file: str,
    ):
        self.logger_name = logger_name
        self.log_file = log_file
        self.context: ServiceContext | None = None

    def bootstrap(self, app: FastAPI | None = None) -> ServiceContext:
        injector.scan_and_load_all("app")

        settings: Settings = injector.get(Settings)

        LogConfig.LOG_DIR.mkdir(parents=True, exist_ok=True)
        logger = LogConfig.setup_logger(
            logger_name=self.logger_name,
            log_file=self.log_file,
            log_level=settings.app.log_level,
            enable_file_logging=settings.app.enable_file_logging,
        )

        self.context = ServiceContext(
            settings=settings,
            logger=logger,
        )

        return self.context

    async def start_runtime_services(self) -> None:
        self._require_context()
        self.context.logger.info("Runtime services started successfully")

    async def stop_runtime_services(self) -> None:
        self._require_context()
        self.context.logger.info("Runtime services stopped successfully")

    def _require_context(self) -> None:
        if self.context is None:
            raise RuntimeError("ServiceManager.bootstrap() must be called first")
