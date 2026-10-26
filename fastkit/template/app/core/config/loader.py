import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import dotenv_values


# app/core/config/loader.py -> app/core/config -> app/core -> app -> repository root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
ENV_FILE = PROJECT_ROOT / ".env"

_ENV_ALIASES = {
    "development": "dev",
    "local": "dev",
    "production": "prod",
}
_ENV_PLACEHOLDER = re.compile(r"^\$\{([A-Za-z_][A-Za-z0-9_]*)\}$")


def get_app_env() -> str:
    dotenv_env = dotenv_values(ENV_FILE).get("APP_ENV") if ENV_FILE.exists() else None
    raw_env = os.getenv("APP_ENV") or dotenv_env or "dev"
    app_env = raw_env.strip().lower()
    return _ENV_ALIASES.get(app_env, app_env)


def get_yaml_config_files() -> list[Path]:
    app_env = get_app_env()
    config_files = [CONFIG_DIR / "default.yml"]

    if app_env != "default":
        environment_config = CONFIG_DIR / f"{app_env}.yml"
        if not environment_config.exists():
            raise FileNotFoundError(
                f"Config file for APP_ENV={app_env!r} was not found: {environment_config}"
            )
        config_files.append(environment_config)

    return config_files


def load_yaml_config() -> dict[str, Any]:
    config: dict[str, Any] = {}
    for config_file in get_yaml_config_files():
        config = _deep_merge(config, _read_yaml_file(config_file))

    # YAML contains non-sensitive defaults. A value written as ${ENV_KEY} is an
    # explicit required value: resolve it from the process environment first,
    # then from .env, and fail before the app starts if it is absent.
    dotenv_values_by_key = dotenv_values(ENV_FILE) if ENV_FILE.exists() else {}
    return _resolve_env_placeholders(config, dotenv_values_by_key)


def _read_yaml_file(config_file: Path) -> dict[str, Any]:
    with config_file.open(encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Config file must contain a YAML mapping: {config_file}")

    return data


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)

    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value

    return merged


def _resolve_env_placeholders(
    value: Any,
    dotenv_values_by_key: dict[str, str | None],
    path: str = "",
) -> Any:
    if isinstance(value, dict):
        return {
            key: _resolve_env_placeholders(
                nested_value,
                dotenv_values_by_key,
                f"{path}.{key}" if path else key,
            )
            for key, nested_value in value.items()
        }

    if isinstance(value, list):
        return [
            _resolve_env_placeholders(item, dotenv_values_by_key, f"{path}[{index}]")
            for index, item in enumerate(value)
        ]

    if not isinstance(value, str):
        return value

    match = _ENV_PLACEHOLDER.fullmatch(value)
    if match is None:
        return value

    env_key = match.group(1)
    resolved = os.getenv(env_key, dotenv_values_by_key.get(env_key))
    if resolved is None or not resolved.strip():
        raise ValueError(
            f"Required environment variable {env_key!r} for configuration key {path!r} is missing"
        )
    return resolved
