"""Install OpenTelemetry tracing into a generated project."""

from pathlib import Path
import shutil
import tomllib

import click

from scaffoldlane.addons.redis.install import _replace


FILES = Path(__file__).parent / "files"
TEMPLATE = Path(__file__).resolve().parents[2] / "template"
REDIS_FILES = Path(__file__).resolve().parents[1] / "redis/files"


def install(project: Path) -> None:
    project = project.resolve()
    if not (project / "app/core/config/root.py").is_file() or not (project / "main.py").is_file():
        raise click.ClickException(f"No generated Scaffoldlane project found at {project}")
    if (project / "app/core/tracing.py").exists() or (project / "app/core/config/tracing.py").exists():
        raise click.ClickException("Tracing is already installed; no files were changed.")

    edits: dict[Path, str] = {}

    def edit(relative: str, changes: list[tuple[str, str]]) -> None:
        path = project / relative
        content = path.read_text(encoding="utf-8")
        for old, new in changes:
            content = _replace(content, old, new, path)
        edits[path] = content

    edit("app/core/config/root.py", [
        ("from .loader import get_app_env, load_yaml_config", "from .tracing import TracingSettings\nfrom .loader import get_app_env, load_yaml_config"),
        ("    database: DatabaseSettings", "    database: DatabaseSettings\n    tracing: TracingSettings = Field(default_factory=TracingSettings)"),
    ])
    edit("app/core/config/__init__.py", [
        ("from .root import Settings", "from .tracing import TracingSettings\nfrom .root import Settings"),
        ('    "Settings",', '    "TracingSettings",\n    "Settings",'),
    ])
    project_name = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))["project"]["name"]
    edit("app/config/default.yml", [
        ("auth:\n", f"tracing:\n  enabled: false\n  service_name: {project_name}\nauth:\n"),
    ])
    edit(".env.example", [
        ("APP_ENV=dev\n", "APP_ENV=dev\n\n# OpenTelemetry tracing (added by scaffoldlane add tracing).\n# TRACING__ENABLED=true\n# TRACING__SERVICE_NAME=your-service-name\n# TRACING__OTLP_TRACES_ENDPOINT=http://localhost:4318/v1/traces\n"),
    ])
    edit("pyproject.toml", [
        ('  "fastapi",', '  "opentelemetry-api", "opentelemetry-sdk",\n  "opentelemetry-exporter-otlp-proto-http",\n  "opentelemetry-instrumentation-fastapi", "opentelemetry-instrumentation-httpx",\n  "fastapi",'),
    ])
    edit("app/core/service_manager.py", [
        ("from app.core.logging.logging_config import LogConfig", "from app.core.logging.logging_config import LogConfig\nfrom app.core.tracing import setup_tracing"),
        ("        self.context = ServiceContext(", "        setup_tracing(settings=settings, logger=logger, app=app)\n\n        self.context = ServiceContext("),
    ])

    targets = {
        "app/core/tracing.py": FILES / "app/core/tracing.py",
        "app/core/config/tracing.py": FILES / "app/core/config/tracing.py",
        "app/core/repository/base_repo.py": FILES / "app/core/repository/base_repo.py",
        "app/core/logging/structured_logging.py": FILES / "app/core/logging/structured_logging.py",
    }
    if (project / "app/core/redis/kv_service.py").is_file():
        targets["app/core/redis/kv_service.py"] = FILES / "app/core/redis/kv_service.py"
    for relative, source in targets.items():
        target = project / relative
        if not source.is_file() or (target.exists() and relative in {"app/core/tracing.py", "app/core/config/tracing.py"}):
            raise click.ClickException(f"Cannot install tracing file: {target}")
        if relative in {"app/core/repository/base_repo.py", "app/core/logging/structured_logging.py", "app/core/redis/kv_service.py"}:
            baseline = (REDIS_FILES if relative.startswith("app/core/redis/") else TEMPLATE) / relative
            if target.read_bytes() != baseline.read_bytes():
                raise click.ClickException(f"Refusing to replace modified file: {target}")
    for relative, source in targets.items():
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    for path, content in edits.items():
        path.write_text(content, encoding="utf-8")
