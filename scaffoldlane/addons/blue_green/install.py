"""Install optional blue-green deployment support."""

from pathlib import Path
import tomllib

import click


FILES = Path(__file__).parent / "files"


def _copy_files(project: Path) -> None:
    sources = [
        source for source in FILES.rglob("*")
        if source.is_file() and "__pycache__" not in source.parts and source.suffix != ".pyc"
    ]
    for source in sources:
        target = project / source.relative_to(FILES)
        if target.exists() and source.relative_to(FILES).as_posix() not in {
            "dev_cli/deployment.py", "deployment/Dockerfile"
        }:
            raise click.ClickException(f"Refusing to overwrite {target}")

    project_name = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))["project"]["name"]
    network_name = f"{project_name}_deployment"
    for source in sources:
        target = project / source.relative_to(FILES)
        target.parent.mkdir(parents=True, exist_ok=True)
        content = source.read_text(encoding="utf-8")
        content = content.replace("__DEPLOYMENT_NETWORK__", network_name)
        target.write_text(content, encoding="utf-8")


def install(project: Path) -> None:
    project = project.resolve()
    required = [
        project / "main.py",
        project / "pyproject.toml",
        project / "deployment/docker-compose.yml",
        project / "dev_cli/main.py",
    ]
    if not all(path.is_file() for path in required):
        raise click.ClickException(f"No generated Scaffoldlane project found at {project}")
    if (project / "deployment/docker-compose.blue.yml").exists():
        raise click.ClickException("Blue-green deployment is already installed; no files were changed.")
    base_deployment = Path(__file__).parents[2] / "template" / "dev_cli" / "deployment.py"
    current_deployment = project / "dev_cli" / "deployment.py"
    if current_deployment.read_text(encoding="utf-8") != base_deployment.read_text(encoding="utf-8"):
        raise click.ClickException(f"Refusing to replace modified {current_deployment}")

    project_name = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))["project"]["name"]
    network_name = f"{project_name}_deployment"
    compose = project / "deployment/docker-compose.yml"
    compose_content = compose.read_text(encoding="utf-8")
    if "  caddy:" in compose_content:
        raise click.ClickException("The deployment Compose file already contains a Caddy service; no files were changed.")
    if "  postgres_data:\n" not in compose_content or (
        "      - ../db/migrations/001_users.sql:/docker-entrypoint-initdb.d/001_users.sql:ro\n"
        not in compose_content
    ):
        raise click.ClickException(f"Cannot find expected Compose integration points in {compose}")
    compose_content = compose_content.replace(
        "  postgres_data:\n",
        "  postgres_data:\n  caddy_data:\n  caddy_config:\n",
    )
    compose_content = compose_content.replace(
        "    depends_on:\n      - postgres\n",
        "    depends_on:\n      - postgres\n    networks:\n      - deployment\n",
        1,
    )
    compose_content = compose_content.replace(
        "      - ../db/migrations/001_users.sql:/docker-entrypoint-initdb.d/001_users.sql:ro\n",
        "      - ../db/migrations/001_users.sql:/docker-entrypoint-initdb.d/001_users.sql:ro\n    networks:\n      - deployment\n",
    )
    caddy_service = """

  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    networks:
      - deployment

"""
    compose_content = compose_content.replace("\nvolumes:\n", caddy_service + "\nvolumes:\n", 1)
    compose_content += """

networks:
  deployment:
    name: __DEPLOYMENT_NETWORK__
"""

    main = project / "dev_cli/main.py"
    main_content = main.read_text(encoding="utf-8")
    main_content = main_content.replace(
        "from dev_cli.deployment import deploy\n",
        "from dev_cli.deployment import deploy, rollback, deployment_status\n",
    )
    main_content = main_content.replace(
        "cli.add_command(generate)\n",
        "cli.add_command(generate)\ncli.add_command(deployment_status)\ncli.add_command(rollback)\n",
    )

    _copy_files(project)
    compose_content = compose_content.replace("__DEPLOYMENT_NETWORK__", network_name)
    compose.write_text(compose_content, encoding="utf-8")
    main.write_text(main_content, encoding="utf-8")
