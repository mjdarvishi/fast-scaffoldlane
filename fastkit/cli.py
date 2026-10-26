from pathlib import Path
import re
import shutil
import subprocess
import sys

import click


TEMPLATE = Path(__file__).resolve().parent / "template"


@click.group()
def cli() -> None:
    """Create FastKit projects from the reusable backbone."""


@cli.command()
@click.argument("name")
@click.option("--destination", type=click.Path(path_type=Path), default=Path.cwd())
@click.option("--git/--no-git", default=True, help="Initialize a Git repository.")
def new(name: str, destination: Path, git: bool) -> None:
    """Create a project with an empty app/features package."""
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


if __name__ == "__main__":
    cli()
