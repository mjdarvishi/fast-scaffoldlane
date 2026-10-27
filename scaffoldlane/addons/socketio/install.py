"""Install the optional Socket.IO integration into a generated project."""

from pathlib import Path
import shutil

import click

from scaffoldlane.addons.redis.install import _replace


FILES = Path(__file__).parent / "files"


def install(project: Path) -> None:
    project = project.resolve()
    main = project / "main.py"
    pyproject = project / "pyproject.toml"
    socketio_dir = project / "app/socketio"
    if not main.is_file() or not pyproject.is_file() or not (project / "app/core/service_manager.py").is_file():
        raise click.ClickException(f"No generated Scaffoldlane project found at {project}")
    if socketio_dir.exists() or "sio_app" in main.read_text(encoding="utf-8"):
        raise click.ClickException("Socket.IO is already installed; no files were changed.")

    main_content = main.read_text(encoding="utf-8")
    main_content = _replace(
        main_content,
        "from fastapi import FastAPI",
        "import uvicorn\nfrom fastapi import FastAPI\nfrom socketio import ASGIApp\n\nfrom app.socketio.instance import sio\nfrom app.socketio.register import register_all_events",
        main,
    )
    main_content += (
        "\n\nregister_all_events(sio)\n"
        "sio_app = ASGIApp(sio, other_asgi_app=app)\n"
        "\n\nif __name__ == \"__main__\":\n"
        "    uvicorn.run(\"main:sio_app\", host=\"0.0.0.0\", port=5010, reload=True)\n"
    )

    pyproject_content = pyproject.read_text(encoding="utf-8")
    pyproject_content = _replace(
        pyproject_content, '  "fastapi",', '  "python-socketio>=5",\n  "fastapi",', pyproject
    )

    for source in FILES.rglob("*"):
        if source.is_file() and (project / source.relative_to(FILES)).exists():
            raise click.ClickException(f"Refusing to overwrite {project / source.relative_to(FILES)}")
    for source in FILES.rglob("*"):
        if source.is_file():
            target = project / source.relative_to(FILES)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    main.write_text(main_content, encoding="utf-8")
    pyproject.write_text(pyproject_content, encoding="utf-8")
