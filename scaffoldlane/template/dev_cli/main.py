import click

from dev_cli.generate import generate


@click.group()
def cli() -> None:
    """Project development commands."""


cli.add_command(generate)


if __name__ == "__main__":
    cli()
