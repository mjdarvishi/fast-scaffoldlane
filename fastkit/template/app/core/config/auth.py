"""Settings for locally issued and verified access tokens."""

from pydantic import BaseModel, Field


class TokenSettings(BaseModel):
    """Shared-secret material for user access tokens."""

    secret_key: str = ""
    access_token_expire_minutes: int = Field(default=60, gt=0)
    issuer: str | None = None
    audience: str | list[str] | None = None

    @property
    def secret_key_value(self) -> str:
        secret = self.secret_key.strip()
        if len(secret.encode()) < 32:
            raise ValueError("access token secret key must be at least 32 bytes")
        return secret


class AuthSettings(BaseModel):
    tokens: TokenSettings = Field(default_factory=TokenSettings)
