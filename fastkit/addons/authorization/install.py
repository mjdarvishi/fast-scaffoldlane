"""Install generic role-based authorization in a generated project."""

from pathlib import Path
import shutil

import click


FILES = Path(__file__).parent / "files"


def install(project: Path) -> None:
    project = project.resolve()
    if not (project / "main.py").is_file() or not (project / "app/core/dependency.py").is_file():
        raise click.ClickException(f"No generated FastKit project found at {project}")
    if (project / "app/core/authorization").exists():
        raise click.ClickException("Authorization is already installed; no files were changed.")
    sources = [source for source in FILES.rglob("*") if source.is_file()]
    for source in sources:
        target = project / source.relative_to(FILES)
        if target.exists():
            raise click.ClickException(f"Refusing to overwrite {target}")
    for source in sources:
        target = project / source.relative_to(FILES)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
