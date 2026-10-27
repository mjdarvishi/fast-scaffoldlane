from pathlib import Path
import re
import shutil
import subprocess
import sys

import click

from fastkit.addons.redis.install import install as install_redis
from fastkit.addons.authorization.install import install as install_authorization
from fastkit.addons.socketio.install import install as install_socketio
from fastkit.addons.tracing.install import install as install_tracing


TEMPLATE = Path(__file__).resolve().parent / "template"
SERVICES = {
    "redis": install_redis,
    "tracing": install_tracing,
    "socketio": install_socketio,
    "authorization": install_authorization,
}


def _choose_services(project: Path) -> None:
    """Offer optional services one at a time until the user is done."""
    remaining = list(SERVICES)
    while remaining:
        click.echo("\nAvailable services:")
        for number, service in enumerate(remaining, 1):
            click.echo(f"  {number}. {service}")
        click.echo("  0. Done")
        choice = click.prompt("Select a service", type=click.IntRange(0, len(remaining)))
        if choice == 0:
            return
        service = remaining.pop(choice - 1)
        SERVICES[service](project)
        click.echo(f"Added {service} to {project.resolve()}.")


@click.group()
def cli() -> None:
    """Create FastKit projects from the reusable backbone."""


@cli.command()
@click.argument("name")
@click.option("--destination", type=click.Path(path_type=Path), default=Path.cwd())
@click.option("--git/--no-git", default=True, help="Initialize a Git repository.")
def new(name: str, destination: Path, git: bool) -> None:
    """Create a project with the default auth feature."""
    if not re.fullmatch(r"[a-z][a-z0-9_]*", name):
        raise click.ClickException("Use a lowercase Python package name, such as inventory_api.")
    target = destination / name
    if target.exists():
        raise click.ClickException(f"Destination already exists: {target}")
    if not TEMPLATE.is_dir():
        raise click.ClickException("Bundled project template is missing.")
    shutil.copytree(TEMPLATE, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for path in target.rglob("*"):
        if path.is_file() and path.suffix in {".toml", ".yml", ".py", ".md", ".example"}:
            content = path.read_text(encoding="utf-8")
            if "__PROJECT_NAME__" in content:
                path.write_text(content.replace("__PROJECT_NAME__", name), encoding="utf-8")
    if git:
        try:
            subprocess.run(
                ["git", "init", "-q", str(target)],
                check=True,
                capture_output=True,
                text=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            raise click.ClickException(f"Project created at {target}, but Git initialization failed: {exc}") from exc
    click.echo(f"Created {target}")
    click.echo("Optional services can also be added later with 'fastkit add'.")
    try:
        if click.confirm("Would you like to add optional services now?", default=False):
            _choose_services(target)
    except (click.Abort, EOFError):
        # Project creation also works when stdin is unavailable (for example in CI).
        if sys.stdin.isatty():
            raise


@cli.command(context_settings={"ignore_unknown_options": True})
@click.option(
    "--project",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path.cwd(),
    help="Generated project directory (defaults to the current directory).",
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def generate(project: Path, args: tuple[str, ...]) -> None:
    """Run feature generators in a generated project."""
    project = project.resolve()
    if not (project / "app" / "features" / "__init__.py").is_file() or not (
        project / "dev_cli" / "main.py"
    ).is_file():
        raise click.ClickException(
            f"No generated project found at {project}. Change to the project directory "
            "or pass --project PATH."
        )
    result = subprocess.run(
        [sys.executable, "-m", "dev_cli.main", "generate", *args], cwd=project, check=False
    )
    if result.returncode:
        raise SystemExit(result.returncode)


@cli.group(invoke_without_command=True)
@click.option("--project", type=click.Path(path_type=Path, file_okay=False),
              default=Path.cwd(), help="Generated project directory.")
@click.pass_context
def add(ctx: click.Context, project: Path) -> None:
    """Install optional integrations in a generated project."""
    if ctx.invoked_subcommand is None:
        _choose_services(project)


@add.command("redis")
@click.option("--project", type=click.Path(path_type=Path, file_okay=False),
              default=Path.cwd(), help="Generated project directory.")
def add_redis(project: Path) -> None:
    """Add Redis connection, key-value service, configuration and Compose service."""
    install_redis(project)
    click.echo(f"Added Redis to {project.resolve()}. Run uv sync in that project.")


@add.command("tracing")
@click.option("--project", type=click.Path(path_type=Path, file_okay=False),
              default=Path.cwd(), help="Generated project directory.")
def add_tracing(project: Path) -> None:
    """Add OpenTelemetry tracing to a generated project."""
    install_tracing(project)
    click.echo(f"Added tracing to {project.resolve()}. Run uv sync in that project.")


@add.command("socketio")
@click.option("--project", type=click.Path(path_type=Path, file_okay=False),
              default=Path.cwd(), help="Generated project directory.")
def add_socketio(project: Path) -> None:
    """Add a generic Socket.IO ASGI server to a generated project."""
    install_socketio(project)
    click.echo(f"Added Socket.IO to {project.resolve()}. Run uv sync in that project.")


@add.command("authorization")
@click.option("--project", type=click.Path(path_type=Path, file_okay=False),
              default=Path.cwd(), help="Generated project directory.")
def add_authorization(project: Path) -> None:
    """Add generic role-based authorization and a reviewable SQL migration."""
    install_authorization(project)
    click.echo(f"Added authorization to {project.resolve()}. Review and apply db/migrations/authorization.sql.")


if __name__ == "__main__":
    cli()
