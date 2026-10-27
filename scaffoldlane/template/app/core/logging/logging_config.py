import logging
import logging.handlers
from pathlib import Path

from app.core.logging.structured_logging import JsonLogFormatter, StructuredContextFilter


class SeparatorRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Compatibility alias for rotating file handler."""

    def emit(self, record):
        super().emit(record)


class LogConfig:
    """Central logging configuration."""

    LOGGER_NAMESPACE = "trainer_equipment"
    API_LOGGER_NAME = f"{LOGGER_NAMESPACE}.api"
    WORKER_LOGGER_NAME = f"{LOGGER_NAMESPACE}.worker"

    LOG_DIR = Path("logs")

    DETAILED_FORMAT = (
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
    SIMPLE_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    DEFAULT_SERVICE_BY_LOGGER = {
        API_LOGGER_NAME: "fastapi",
        WORKER_LOGGER_NAME: "hub",
    }

    @staticmethod
    def setup_logger(
        logger_name: str,
        log_file: str,
        log_level: str = "INFO",
        enable_file_logging: bool = True,
        service_name: str | None = None,
    ) -> logging.Logger:
        """
        Create a dedicated logger with its own file.

        Args:
            logger_name: unique logger name (e.g. trainer_equipment.api)
            log_file: filename (e.g. api.log)
        """

        LogConfig.LOG_DIR.mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # 🚨 VERY IMPORTANT → prevents logs going to root logger
        logger.propagate = False

        # Clear existing handlers
        if logger.hasHandlers():
            logger.handlers.clear()

        formatter = JsonLogFormatter()
        service = service_name or LogConfig.DEFAULT_SERVICE_BY_LOGGER.get(logger_name, "fastapi")
        context_filter = StructuredContextFilter(service_name=service)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.addFilter(context_filter)
        logger.addHandler(console_handler)

        if enable_file_logging:
            # Main log file (api.log or worker.log)
            file_handler = SeparatorRotatingFileHandler(
                LogConfig.LOG_DIR / log_file,
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
            )
            file_handler.setFormatter(formatter)
            file_handler.addFilter(context_filter)
            logger.addHandler(file_handler)

            # Shared error log
            error_handler = SeparatorRotatingFileHandler(
                LogConfig.LOG_DIR / "error.log",
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            error_handler.addFilter(context_filter)
            logger.addHandler(error_handler)

        return logger

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(name)

    @staticmethod
    def get_app_logger() -> logging.Logger:
        return logging.getLogger(LogConfig.API_LOGGER_NAME)

    @staticmethod
    def get_worker_logger() -> logging.Logger:
        return logging.getLogger(LogConfig.WORKER_LOGGER_NAME)
