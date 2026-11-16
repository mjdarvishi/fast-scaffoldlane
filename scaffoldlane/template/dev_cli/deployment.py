"""Standard deployment for generated projects."""

from pathlib import Path
import subprocess

import click


@click.group()
def deploy() -> None:
    """Deploy the application."""


@deploy.command("normal")
def deploy_normal() -> None:
    """Build and start the standard application and database stack."""
    project = Path.cwd()
    compose = project / "deployment" / "docker-compose.yml"
    if not compose.is_file():
        raise click.ClickException(f"Missing {compose}")
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
