"""Provider-neutral claims accepted from authenticated JWTs."""

from pydantic import BaseModel, ConfigDict, Field


class JwtClaims(BaseModel):
    """The standard identity claim this application needs from a JWT.

    Provider-specific claims are retained so features can opt into them explicitly
    without coupling the shared authentication layer to one identity provider.
    """

    model_config = ConfigDict(extra="allow", strict=True)

    sub: str = Field(min_length=1)
