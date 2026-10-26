from fastapi import Request

from app.core.config import Settings
from app.core.dependency import injector
from app.core.exception import (
    AccessDeniyedException,
    AlreadyExistException,
    BadRequesException,
    CommunicationException,
    DataBaseException,
    NotFoundException,
)
from app.core.logging.logging_config import LogConfig
from app.core.logging.structured_logging import get_or_create_trace_id
from app.core.reponse import CustomResponse

logger = LogConfig.get_app_logger()
setting = injector.get(Settings)


def log_error(error_code, exc, request: Request = None):
    log_data = {
        "event": "request_error",
        "error_code": error_code,
        "error": str(exc),
    }
    if request:
        log_data.update(
            {
                "path": str(request.url.path),
                "method": request.method,
                "query": dict(request.query_params),
                "client_ip": request.client.host if request.client else None,
            }
        )
    logger.error("request_error", extra={"event_data": log_data}, exc_info=True)


async def global_exception_handler(request: Request, exc: Exception):
    error_code = get_or_create_trace_id()
    log_error(error_code, exc, request)
    if setting.app.debug:
        return CustomResponse.internal_server_error(body={"code": error_code, "detail": str(exc)})
    else:
        return CustomResponse.internal_server_error(
            body={"code": error_code, "detail": "Internal Server Error"}
        )


async def database_exception_handler(request: Request, exc: DataBaseException):
    if setting.app.debug:
        log_error(exc.error_code, exc, request)
        return CustomResponse.failed(
            message={
                "desc": "DataBaseException-DataIntegrity",
                "code": exc.error_code,
            },
            body=exc.message,
            status_code=401,
        )
    else:
        return CustomResponse.failed(
            message={
                "desc": "DataBaseException-DataIntegrity",
                "code": exc.error_code,
            },
            body="Data Integrity Error",
            status_code=401,
        )


async def access_denied_exception_handler(request: Request, exc: AccessDeniyedException):
    log_error(exc.error_code, exc, request)
    return CustomResponse.failed(
        message="AccessDeniyedException",
        body={"desc": exc.message, "code": exc.error_code},
        status_code=403,
    )


async def duplicate_exception_handler(request: Request, exc: AlreadyExistException):
    log_error(exc.error_code, exc, request)
    return CustomResponse.failed(
        message="AlreadyExistException",
        body={"desc": exc.message, "code": exc.error_code},
        status_code=409,
    )


async def bad_request_exception_handler(request: Request, exc: BadRequesException):
    log_error(exc.error_code, exc, request)
    return CustomResponse.failed(
        message="BadRequesException",
        body={"desc": exc.message, "code": exc.error_code},
        status_code=400,
    )


async def not_found_exception_handler(request: Request, exc: NotFoundException):
    log_error(exc.error_code, exc, request)
    return CustomResponse.failed(
        message="NotFoundException",
        body={"desc": exc.message, "code": exc.error_code},
        status_code=404,
    )


async def communication_exception_handler(request: Request, exc: CommunicationException):
    log_error(exc.error_code, exc, request)
    if setting.app.debug:
        return CustomResponse.failed(
            message=f"CommunicationException:{exc.error_content}",
            body={"code": exc.error_code, "desc": exc.message},
            status_code=522,
        )

    return CustomResponse.failed(
        message="CommunicationException",
        body={"code": exc.error_code, "desc": "External service communication failed"},
        status_code=522,
    )


def register_exception_handlers(app):
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(DataBaseException, database_exception_handler)
    app.add_exception_handler(AccessDeniyedException, access_denied_exception_handler)
    app.add_exception_handler(AlreadyExistException, duplicate_exception_handler)
    app.add_exception_handler(BadRequesException, bad_request_exception_handler)
    app.add_exception_handler(NotFoundException, not_found_exception_handler)
    app.add_exception_handler(CommunicationException, communication_exception_handler)
