"""Blue-green deployment commands for generated projects."""

from pathlib import Path
import re
import subprocess
import time

import click


COLORS = ("blue", "green")
UPSTREAM_PATTERN = re.compile(r"(reverse_proxy\s+)app-(blue|green)(:8000)")


def _paths() -> tuple[Path, Path, Path]:
    project = Path.cwd()
    deployment = project / "deployment"
    return project, deployment / "docker-compose.yml", deployment


def _compose(project: Path, compose_file: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["docker", "compose", "--project-name", project.name, "--file", str(compose_file), *args],
            cwd=project,
            check=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise click.ClickException("Docker Compose was not found in PATH.") from exc


def _validate_color(color: str) -> str:
    if color not in COLORS:
        raise click.ClickException(f"Color must be one of: {', '.join(COLORS)}")
    return color


def _active_color(deployment: Path) -> str:
    state = deployment / ".active-color"
    if state.is_file():
        return _validate_color(state.read_text(encoding="utf-8").strip())
    caddyfile = deployment / "Caddyfile"
    match = re.search(r"reverse_proxy\s+app-(blue|green):8000", caddyfile.read_text(encoding="utf-8"))
    if match is None:
        raise click.ClickException(f"Cannot determine the active color from {caddyfile}")
    return match.group(1)


def _wait_until_healthy(project: Path, compose_file: Path, service: str, timeout: int = 120) -> None:
    container_id = _compose(project, compose_file, "ps", "-q", service).stdout.strip()
    if not container_id:
        raise click.ClickException(f"Compose did not create a container for {service}.")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Health.Status}}", container_id],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).stdout.strip()
        if status == "healthy":
            return
        if status == "unhealthy":
            raise click.ClickException(f"{service} became unhealthy.")
        time.sleep(2)
    raise click.ClickException(f"Timed out waiting for {service} to become healthy.")


def _switch_caddy(project: Path, deployment: Path, color: str) -> None:
    caddyfile = deployment / "Caddyfile"
    old_content = caddyfile.read_text(encoding="utf-8")
    new_content, replacements = UPSTREAM_PATTERN.subn(rf"\1app-{color}\3", old_content, count=1)
    if replacements != 1:
        raise click.ClickException(f"Cannot find an active reverse proxy in {caddyfile}")
    caddyfile.write_text(new_content, encoding="utf-8")
    try:
        _compose(
            project,
            deployment / "docker-compose.yml",
            "exec",
            "-T",
            "caddy",
            "caddy",
            "reload",
            "--config",
            "/etc/caddy/Caddyfile",
            "--adapter",
            "caddyfile",
        )
    except subprocess.CalledProcessError as exc:
        caddyfile.write_text(old_content, encoding="utf-8")
        raise click.ClickException("Caddy reload failed; the previous route was restored.") from exc


def _run_deployment(color: str, remove_old: bool) -> None:
    project, base_compose, deployment = _paths()
    color = _validate_color(color)
    color_compose = deployment / f"docker-compose.{color}.yml"
    if not base_compose.is_file() or not color_compose.is_file():
        raise click.ClickException("Blue-green deployment is not installed in this project.")

    active = _active_color(deployment)
    if active == color:
        raise click.ClickException(f"{color} is already active.")
    old_service = f"app-{active}"
    new_service = f"app-{color}"

    _compose(project, base_compose, "up", "-d", "postgres", "caddy")
    _compose(project, color_compose, "up", "-d", "--build", new_service)
    _wait_until_healthy(project, color_compose, new_service)
    _switch_caddy(project, deployment, color)
    (deployment / ".active-color").write_text(color, encoding="utf-8")

    if remove_old:
        _compose(project, deployment / f"docker-compose.{active}.yml", "rm", "--stop", "--force", old_service)
    click.echo(f"Traffic switched to {color}.")


@click.group()
def deploy() -> None:
    """Deploy the project."""


@deploy.command("normal")
def deploy_normal() -> None:
    """Build and start the standard application and database stack."""
    project, compose, _ = _paths()
    try:
        subprocess.run(
            ["docker", "compose", "--project-name", project.name, "--file", str(compose),
             "up", "-d", "--build", "postgres", "app"],
            cwd=project, check=True,
        )
    except FileNotFoundError as exc:
        raise click.ClickException("Docker Compose was not found in PATH.") from exc
    except subprocess.CalledProcessError as exc:
        raise click.ClickException(f"Deployment failed with exit code {exc.returncode}.") from exc
    click.echo("Standard deployment is running on port 8000.")


@deploy.command("blue-green")
@click.option("--color", type=click.Choice(COLORS), help="Color to deploy instead of the inactive color.")
def deploy_blue_green(color: str | None) -> None:
    """Deploy the inactive blue-green environment."""
    _, _, deployment = _paths()
    _run_deployment(color or ("green" if _active_color(deployment) == "blue" else "blue"), remove_old=True)


@click.group()
def rollback() -> None:
    """Roll back the project deployment."""


@rollback.command("blue-green")
def rollback_blue_green() -> None:
    """Switch traffic back to the inactive blue-green environment."""
    _, _, deployment = _paths()
    active = _active_color(deployment)
    target = "green" if active == "blue" else "blue"
    _run_deployment(target, remove_old=True)


@click.command("deployment-status")
def deployment_status() -> None:
    """Show the active blue-green environment."""
    _, _, deployment = _paths()
    click.echo(f"Active color: {_active_color(deployment)}")
