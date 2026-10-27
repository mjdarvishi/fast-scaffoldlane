"""FastAPI dependencies for JWT-authenticated requests."""

from uuid import UUID

from fastapi import Request

from app.core.exception.base_exception import AccessDeniyedException

from .claims import JwtClaims
from .tokens import strip_bearer, verify_jwt


def load_principal(token: str) -> JwtClaims:
    """Verify a raw JWT, including when called outside an HTTP request."""
    return verify_jwt(token)


def get_current_principal(request: Request) -> JwtClaims:
    """Return the principal parsed once by the authentication middleware."""
    principal = getattr(request.state, "principal", None)
    if principal is not None:
        return principal

    authentication_error = getattr(request.state, "authentication_error", None)
    if authentication_error is not None:
        raise authentication_error

    if not request.headers.get("Authorization"):
        raise AccessDeniyedException(message="Missing Authorization header")

    # Supports direct dependency invocation in tests where middleware is absent.
    return load_principal(strip_bearer(request.headers["Authorization"]))


def get_current_user_id(request: Request) -> UUID:
    """Return the UUID identity made available by authentication middleware."""
    get_current_principal(request)
    user_id = getattr(request.state, "user_id", None)
    if user_id is not None:
        return user_id

    try:
        return UUID(get_current_principal(request).sub)
    except ValueError as exc:
        raise AccessDeniyedException(message="Invalid authenticated user") from exc
