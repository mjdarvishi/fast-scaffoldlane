from pydantic import BaseModel, Field


class RedisSettings(BaseModel):
    host: str = "localhost"
    port: int = Field(default=6379, ge=1, le=65535)
    db: int = Field(default=0, ge=0)
    password: str | None = None
    reconnect_delay_seconds: int = Field(default=5, ge=1)
