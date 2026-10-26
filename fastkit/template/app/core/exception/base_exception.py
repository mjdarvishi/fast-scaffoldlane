from sqlalchemy import exc as asqlexc

from app.core.logging.structured_logging import get_or_create_trace_id


class BaseError(Exception):
    message: str = "Server Internal Error"

    def __init__(self, message: str | None = None, error_code: str | None = None):
        self.message = message or self.message
        self.error_code = error_code or get_or_create_trace_id()
        super().__init__(self.message)

    def __str__(self):
        return self.message


class AccessDeniyedException(BaseError):
    message: str = "Access deniyed"

    def __init__(self, message):
        super().__init__(message=message)


class AlreadyExistException(BaseError):
    message: str = "Item is alrewady exist"

    def __init__(self, message):
        super().__init__(message=message)


class BadRequesException(BaseError):
    message: str = "Bad Request"

    def __init__(self, message):
        super().__init__(message=message)


class NotFoundException(BaseError):
    message: str = "Item Not Found"

    def __init__(self, message):
        super().__init__(message=message)


class DataBaseException(BaseError):
    def __init__(self, exc: Exception, message: str | None = None):
        if type(exc) is not asqlexc.IntegrityError:
            super().__init__(message=message if message else str(exc))
        else:
            super().__init__(message=message if message else str(exc.orig))
        self.message = message if message else str(exc)


class CommunicationException(BaseError):
    message: str = "Communication with external service failed"
    error_content: str = ""

    def __init__(self, message, error_message: str = ""):
        super().__init__(message=message)
        self.error_content = error_message
