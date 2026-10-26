"""JWT issuance and verification independent of a specific identity provider or feature."""

from datetime import UTC, datetime, timedelta

import jwt
from pydantic import ValidationError

from app.core.config import Settings
from app.core.dependency import injector
from app.core.exception.base_exception import AccessDeniyedException

from .claims import JwtClaims


def create_access_token(*, subject: str) -> tuple[str, int]:
    """Create a signed access token for a local user account."""
    settings = injector.get(Settings).auth.tokens
    now = datetime.now(UTC)
    expires_in = settings.access_token_expire_minutes * 60
    payload: dict[str, object] = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    if settings.issuer is not None:
        payload["iss"] = settings.issuer
    if settings.audience is not None:
        payload["aud"] = settings.audience

    token = jwt.encode(
        payload,
        settings.secret_key_value,
        algorithm="HS256",
    )
    return token, expires_in


def strip_bearer(value: str) -> str:
    """Return the raw token from a Bearer authorization value."""
    scheme, _, token = value.strip().partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise AccessDeniyedException(message="Invalid Authorization header")
    return token.strip()


def verify_jwt(token: str) -> JwtClaims:
    """Verify a JWT and return its provider-neutral authenticated principal."""
    settings = injector.get(Settings).auth.tokens
    decode_options = {"require": ["sub", "exp"]}
    decode_kwargs: dict[str, object] = {}
    if settings.audience is None:
        decode_options["verify_aud"] = False
    else:
        decode_kwargs["audience"] = settings.audience
    if settings.issuer is None:
        decode_options["verify_iss"] = False
    else:
        decode_kwargs["issuer"] = settings.issuer

    try:
        raw_claims = jwt.decode(
            token,
            settings.secret_key_value,
            algorithms=["HS256"],
            options=decode_options,
            **decode_kwargs,
        )
    except jwt.ExpiredSignatureError as exc:
        raise AccessDeniyedException(message="Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise AccessDeniyedException(message="Invalid token") from exc

    try:
        return JwtClaims.model_validate(raw_claims)
    except ValidationError as exc:
        raise AccessDeniyedException(message="Invalid token payload") from exc
