import argparse
import sys

from .generator import create_domain, create_listener, create_model
from .names import normalize_domain_name, normalize_listener_name, normalize_model_name


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate feature scaffolds.\n"
            "- Default mode: create a full new domain under app/features.\n"
            "- --add-model mode: create an entity in an existing domain."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python generate_domain.py --name alarm\n"
            "  python generate_domain.py --name alarm --force\n"
            "  python generate_domain.py --add-model --domain installation --model procedure_rule\n"
            "  python generate_domain.py --add-model --domain installation "
            "--model procedure_rule --force\n"
            "  python generate_domain.py --add-model  # interactive mode\n"
            "  python generate_domain.py --add-listener --domain event "
            "--listener incoming_event --event app.core.event_bus:BaseEvent"
        ),
    )
    parser.add_argument("-n", "--name", help="Domain name (example: alarm, ticketing)")
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite files if the domain folder already exists.",
    )
    parser.add_argument(
        "--add-model",
        dest="add_model",
        action="store_true",
        help="Create an entity inside an existing domain and update __init__.py exports.",
    )
    parser.add_argument(
        "--domain",
        help="Existing domain name for --add-model mode (example: installation).",
    )
    parser.add_argument(
        "--model",
        help="Model name for --add-model mode (example: procedure_category).",
    )
    parser.add_argument(
        "--add-listener",
        action="store_true",
        help="Create an event listener inside an existing domain and update domain registration.",
    )
    parser.add_argument(
        "--listener",
        help="Listener name for --add-listener mode (example: incoming_event).",
    )
    parser.add_argument(
        "--event",
        default="app.core.event_bus:BaseEvent",
        help="Event class import path for --add-listener mode (example: app.core.event_bus:BaseEvent).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    if args.add_model:
        raw_domain = args.domain
        raw_model = args.model

        if not raw_domain:
            raw_domain = input("Enter existing domain name: ").strip()
        if not raw_model:
            raw_model = input("Enter model name: ").strip()

        try:
            domain_name = normalize_domain_name(raw_domain)
            model_name = normalize_model_name(raw_model)
        except ValueError as exc:
            print(f"Error: {exc}")
            return 1

        try:
            entity_file = create_model(domain_name, model_name, force=args.force)
        except (FileExistsError, FileNotFoundError) as exc:
            print(f"Error: {exc}")
            return 1

        print(f"Model scaffold created successfully for domain '{domain_name}'.")
        print(f"Entity: {entity_file}")
        return 0

    if args.add_listener:
        raw_domain = args.domain
        raw_listener = args.listener

        if not raw_domain:
            raw_domain = input("Enter existing domain name: ").strip()
        if not raw_listener:
            raw_listener = input("Enter listener name: ").strip()

        try:
            domain_name = normalize_domain_name(raw_domain)
            listener_name = normalize_listener_name(raw_listener)
        except ValueError as exc:
            print(f"Error: {exc}")
            return 1

        try:
            listener_file = create_listener(
                domain_name,
                listener_name,
                event_import_path=args.event,
                force=args.force,
            )
        except (FileExistsError, FileNotFoundError, ValueError) as exc:
            print(f"Error: {exc}")
            return 1

        print(f"Listener scaffold created successfully for domain '{domain_name}'.")
        print(f"Listener: {listener_file}")
        return 0

    raw_name = args.name
    if not raw_name:
        raw_name = input("Enter new domain name: ").strip()

    try:
        domain_name = normalize_domain_name(raw_name)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    try:
        created_path = create_domain(domain_name, force=args.force)
    except FileExistsError as exc:
        print(f"Error: {exc}")
        return 1

    print(f"Domain scaffold created successfully at: {created_path}")
    print("Remember to register the new domain in main.py if needed.")
    return 0
