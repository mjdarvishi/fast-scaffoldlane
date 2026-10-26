from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    EnvSettingsSource,
    InitSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from app.core.dependency import injectable

from .app import AppSettings
from .auth import AuthSettings
from .database import DatabaseSettings
from .loader import get_app_env, load_yaml_config
from .tracing import TracingSettings


@injectable(singleton=True)
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__", extra="ignore")

    # Name, version and description are build-time facts rather than settings: they
    # live only in pyproject.toml and are read through app.core.project.
    app_env: str = Field(default_factory=get_app_env)
    app: AppSettings = Field(default_factory=AppSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    database: DatabaseSettings
    tracing: TracingSettings = Field(default_factory=TracingSettings)

    @property
    def is_dev(self) -> bool:
        return self.app_env == "dev"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: EnvSettingsSource,
        dotenv_settings: DotEnvSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        yaml_settings = InitSettingsSource(settings_cls, load_yaml_config())
        return init_settings, env_settings, dotenv_settings, yaml_settings, file_secret_settings
