import click

from dev_cli import file_generator


@click.group()
def generate() -> None:
    """Generate project scaffolding."""


@generate.command("domain")
@click.argument("name", required=False)
@click.option("-f", "--force", is_flag=True, help="Overwrite files if the domain exists.")
def generate_domain(name: str | None, force: bool) -> None:
    """Create a complete feature domain using the project file generator."""
    raw_name = name or click.prompt("Enter new domain name")

    try:
        domain_name = file_generator.normalize_domain_name(raw_name)
        created_path = file_generator.create_domain(domain_name, force=force)
    except (ValueError, FileExistsError) as exc:
        raise click.ClickException(str(exc)) from exc

    click.secho(f"Domain scaffold created: {created_path}", fg="green")
    click.echo("Register the new domain router in app/api/v1/__init__.py if needed.")


@generate.command("model")
@click.argument("domain", required=False)
@click.argument("model", required=False)
@click.option("-f", "--force", is_flag=True, help="Overwrite files if model files exist.")
def generate_model(domain: str | None, model: str | None, force: bool) -> None:
    """Create a domain entity using the project file generator."""
    raw_domain = domain or click.prompt("Enter existing domain name")
    raw_model = model or click.prompt("Enter model name")

    try:
        domain_name = file_generator.normalize_domain_name(raw_domain)
        model_name = file_generator.normalize_model_name(raw_model)
        entity_file = file_generator.create_model(domain_name, model_name, force=force)
    except (ValueError, FileExistsError, FileNotFoundError) as exc:
        raise click.ClickException(str(exc)) from exc

    click.secho(f"Model scaffold created for domain '{domain_name}'.", fg="green")
    click.echo(f"Entity: {entity_file}")


@generate.command("listener")
@click.argument("domain", required=False)
@click.argument("listener", required=False)
@click.option(
    "--event",
    "event_import_path",
    default="app.core.event_bus:BaseEvent",
    show_default=True,
    help="Event class import path in module.path:EventClass format.",
)
@click.option("-f", "--force", is_flag=True, help="Overwrite listener file if it exists.")
def generate_listener(
    domain: str | None,
    listener: str | None,
    event_import_path: str,
    force: bool,
) -> None:
    """Create an event listener and register it on the domain."""
    raw_domain = domain or click.prompt("Enter existing domain name")
    raw_listener = listener or click.prompt("Enter listener name")

    try:
        domain_name = file_generator.normalize_domain_name(raw_domain)
        listener_name = file_generator.normalize_listener_name(raw_listener)
        listener_file = file_generator.create_listener(
            domain_name,
            listener_name,
            event_import_path=event_import_path,
            force=force,
        )
    except (ValueError, FileExistsError, FileNotFoundError) as exc:
        raise click.ClickException(str(exc)) from exc

    click.secho(f"Listener scaffold created for domain '{domain_name}'.", fg="green")
    click.echo(f"Listener: {listener_file}")
