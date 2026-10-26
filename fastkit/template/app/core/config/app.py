from pydantic import BaseModel, Field


class AppSettings(BaseModel):
    debug: bool = False
    call_timeout: int = 10
    log_level: str = "INFO"
    enable_file_logging: bool = True
    allowed_origins: list[str] = Field(default_factory=lambda: ["*"])
