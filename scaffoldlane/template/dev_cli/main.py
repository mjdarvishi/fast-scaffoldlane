import click

from dev_cli.commands import config, db, docker, format_code, lint, run, test, version
from dev_cli.deployment import deploy
from dev_cli.generate import generate


@click.group()
def cli() -> None:
    """Project development commands."""


cli.add_command(generate)
for command in (config, db, docker, format_code, lint, run, test, version, deploy):
    cli.add_command(command)


if __name__ == "__main__":
    cli()
