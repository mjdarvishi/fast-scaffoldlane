"""Install the optional Redis integration into a generated project."""

from pathlib import Path
import shutil

import click


FILES = Path(__file__).parent / "files"


def _replace(content: str, old: str, new: str, path: Path) -> str:
    if old not in content:
        raise click.ClickException(f"Cannot find expected integration point in {path}")
    return content.replace(old, new, 1)


def install(project: Path) -> None:
    project = project.resolve()
    if not (project / "app/core/config/root.py").is_file() or not (project / "main.py").is_file():
        raise click.ClickException(f"No generated FastKit project found at {project}")
    if (project / "app/core/redis").exists() or (project / "app/core/config/redis.py").exists():
        raise click.ClickException("Redis is already installed; no files were changed.")

    edits: dict[Path, str] = {}

    def edit(relative: str, changes: list[tuple[str, str]]) -> None:
        path = project / relative
        content = path.read_text(encoding="utf-8")
        for old, new in changes:
            content = _replace(content, old, new, path)
        edits[path] = content

    edit("app/core/config/root.py", [
        ("from .loader import get_app_env, load_yaml_config", "from .redis import RedisSettings\nfrom .loader import get_app_env, load_yaml_config"),
        ("    database: DatabaseSettings", "    database: DatabaseSettings\n    redis: RedisSettings = Field(default_factory=RedisSettings)"),
    ])
    edit("app/core/config/__init__.py", [
        ("from .root import Settings", "from .redis import RedisSettings\nfrom .root import Settings"),
        ('    "Settings",', '    "RedisSettings",\n    "Settings",'),
    ])
    edit("app/config/default.yml", [
        ("auth:\n", "redis:\n  host: localhost\n  port: 6379\n  db: 0\n  reconnect_delay_seconds: 5\nauth:\n"),
    ])
    edit(".env.example", [
        ("APP_ENV=dev\n", "APP_ENV=dev\n# REDIS__PASSWORD=\n"),
    ])
    edit("pyproject.toml", [
        ('  "fastapi",', '  "redis>=5",\n  "fastapi",'),
    ])
    edit("docker-compose.yml", [
        ("  postgres:\n", "  redis:\n    image: redis:7-alpine\n    ports:\n      - \"6379:6379\"\n  postgres:\n"),
    ])
    edit("app/core/service_manager.py", [
        ("from app.core.dependency import injector", "from app.core.dependency import injector\nfrom app.core.redis.connection import MainRedisConnection"),
        ('        self.context.logger.info("Runtime services started successfully")',
         '        await injector.get(MainRedisConnection).connect()\n        self.context.logger.info("Runtime services started successfully")'),
        ('        self.context.logger.info("Runtime services stopped successfully")',
         '        await injector.get(MainRedisConnection).close()\n        self.context.logger.info("Runtime services stopped successfully")'),
    ])

    # Validate every integration point before writing anything.
    for source in FILES.rglob("*"):
        if source.is_file() and (project / source.relative_to(FILES)).exists():
            raise click.ClickException(f"Refusing to overwrite {project / source.relative_to(FILES)}")
    for source in FILES.rglob("*"):
        if source.is_file():
            target = project / source.relative_to(FILES)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    traced_kv = Path(__file__).parent.parent / "tracing/files/app/core/redis/kv_service.py"
    if (project / "app/core/tracing.py").is_file():
        shutil.copy2(traced_kv, project / "app/core/redis/kv_service.py")
    for path, content in edits.items():
        path.write_text(content, encoding="utf-8")
