"""Everyday commands for a generated Fastkit project."""

import asyncio
import hashlib
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import asyncpg
import click
from dotenv import dotenv_values


ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "deployment" / "docker-compose.yml"


def _run(*args: str) -> None:
    try:
        subprocess.run(args, cwd=ROOT, check=True)
    except FileNotFoundError as exc:
        raise click.ClickException(f"Command not found: {args[0]}") from exc
    except subprocess.CalledProcessError as exc:
        raise click.ClickException(f"Command failed with exit code {exc.returncode}: {' '.join(args)}") from exc


@click.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8000, show_default=True, type=int)
@click.option("--reload/--no-reload", default=True, show_default=True)
def run(host: str, port: int, reload: bool) -> None:
    """Run the FastAPI application locally."""
    args = [sys.executable, "-m", "uvicorn", "main:app", "--host", host, "--port", str(port)]
    if reload:
        args.append("--reload")
    _run(*args)


@click.command()
@click.option("--fix", is_flag=True)
def lint(fix: bool) -> None:
    """Check Python code with Ruff."""
    _run(sys.executable, "-m", "ruff", "check", ".", *(["--fix"] if fix else []))


@click.command("format")
def format_code() -> None:
    """Format Python code with Ruff."""
    _run(sys.executable, "-m", "ruff", "format", ".")


@click.command("test", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("pytest_args", nargs=-1, type=click.UNPROCESSED)
def test(pytest_args: tuple[str, ...]) -> None:
    """Run pytest, forwarding extra arguments."""
    _run(sys.executable, "-m", "pytest", *pytest_args)


@click.group()
def docker() -> None:
    """Manage the local Docker Compose stack."""


@docker.command("up")
@click.option("--build", is_flag=True)
@click.option("-d", "--detach", is_flag=True)
def docker_up(build: bool, detach: bool) -> None:
    """Start local services."""
    _run("docker", "compose", "-f", str(COMPOSE), "up", *(["--build"] if build else []), *(["-d"] if detach else []))


@docker.command("down")
def docker_down() -> None:
    """Stop local services while keeping database data."""
    _run("docker", "compose", "-f", str(COMPOSE), "down")


@click.group()
def config() -> None:
    """Manage project configuration."""


@config.command("init")
def config_init() -> None:
    """Create .env or add missing keys from .env.example."""
    source = ROOT / ".env.example"
    target = ROOT / ".env"
    if not source.is_file():
        raise click.ClickException(f"Missing {source}")
    existing = {key: value for key, value in dotenv_values(target).items() if value is not None}
    additions = []
    for line in source.read_text(encoding="utf-8").splitlines():
        if line and not line.lstrip().startswith("#") and "=" in line:
            key = line.split("=", 1)[0]
            if key not in existing:
                additions.append(line)
    if additions:
        prefix = target.read_text(encoding="utf-8").rstrip() + "\n" if target.exists() else ""
        target.write_text(prefix + "\n".join(additions) + "\n", encoding="utf-8")
    click.echo(f"Added {len(additions)} settings to {target.name}.")


@click.group("db")
def db() -> None:
    """Manage SQL migrations."""


@db.command("migrate")
def db_migrate() -> None:
    """Apply pending SQL migrations with checksum tracking."""
    try:
        asyncio.run(_migrate())
    except (asyncpg.PostgresError, OSError, ValueError) as exc:
        raise click.ClickException(f"Database migration failed: {exc}") from exc


async def _migrate() -> None:
    from app.core.config import Settings

    settings = Settings().database
    migrations = sorted((ROOT / "db" / "migrations").glob("*.sql"))
    connection = await asyncpg.connect(host=settings.host, port=settings.port, user=settings.user,
                                       password=settings.password, database=settings.name)
    applied = 0
    try:
        await connection.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version text PRIMARY KEY, checksum text NOT NULL, applied_at timestamptz NOT NULL DEFAULT now())")
        for path in migrations:
            sql = path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
            old = await connection.fetchval("SELECT checksum FROM schema_migrations WHERE version=$1", path.stem)
            if old == checksum:
                continue
            if old is not None:
                raise click.ClickException(f"Migration changed after application: {path.name}")
            async with connection.transaction():
                await connection.execute(sql)
                await connection.execute("INSERT INTO schema_migrations(version, checksum) VALUES($1, $2)", path.stem, checksum)
            applied += 1
    finally:
        await connection.close()
    click.echo(f"Applied {applied} migration(s).")


@click.command("version")
@click.option("--set", "value")
@click.option("--bump", type=click.Choice(("major", "minor", "patch")))
def version(value: str | None, bump: str | None) -> None:
    """Update the project version in pyproject.toml."""
    if bool(value) == bool(bump):
        raise click.ClickException("Specify exactly one of --set or --bump.")
    path = ROOT / "pyproject.toml"
    current = tomllib.loads(path.read_text(encoding="utf-8"))["project"]["version"]
    if bump:
        if not re.fullmatch(r"\d+\.\d+\.\d+", current):
            raise click.ClickException(f"Cannot bump non-semantic version: {current}")
        parts = [int(part) for part in current.split(".")]
        index = ("major", "minor", "patch").index(bump)
        parts[index] += 1
        for later in range(index + 1, 3):
            parts[later] = 0
        value = ".".join(map(str, parts))
    if not re.fullmatch(r"\d+\.\d+\.\d+", value or ""):
        raise click.ClickException("Version must be MAJOR.MINOR.PATCH.")
    content = path.read_text(encoding="utf-8")
    updated = re.sub(r'(?m)^(version\s*=\s*)"[^"]+"', rf'\g<1>"{value}"', content, count=1)
    if updated == content:
        raise click.ClickException("Project version was not found.")
    path.write_text(updated, encoding="utf-8")
    click.echo(f"{current} -> {value}")
