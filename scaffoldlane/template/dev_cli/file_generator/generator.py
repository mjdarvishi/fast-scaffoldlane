import re
from pathlib import Path

from .names import to_pascal_case
from .templates import render_listener_templates, render_model_templates, render_templates

ROOT_DIR = Path.cwd()
FEATURES_DIR = ROOT_DIR / "app" / "features"


def refresh_folder_init(folder: Path) -> None:
    init_file = folder / "__init__.py"
    class_pattern = re.compile(r"^class (\w+)\b", re.MULTILINE)
    py_files = [f for f in folder.glob("*.py") if f.name != "__init__.py"]

    all_classes = []
    import_lines = []
    for py_file in py_files:
        code = py_file.read_text(encoding="utf-8")
        classes = class_pattern.findall(code)
        if classes:
            import_lines.append(f"from .{py_file.stem} import {', '.join(classes)}")
            all_classes.extend(classes)

    content = "\n".join(import_lines)
    if all_classes:
        content += f"\n\n__all__ = {all_classes!r}\n"
    else:
        content += "\n__all__ = []\n"

    init_file.write_text(content.strip() + "\n", encoding="utf-8")


def listener_class_name(listener: str) -> str:
    class_name = to_pascal_case(listener)
    if not class_name.endswith("Listener"):
        class_name += "Listener"
    return class_name


def parse_event_import(import_path: str) -> tuple[str, str]:
    module_path, separator, class_name = import_path.partition(":")
    if not separator:
        module_path, separator, class_name = import_path.rpartition(".")
    if not module_path or not class_name:
        raise ValueError("Event import must use module.path:EventClass format.")
    return f"from {module_path} import {class_name}", class_name


def listener_classes_in(folder: Path) -> list[str]:
    class_pattern = re.compile(r"^class (\w+Listener)\b", re.MULTILINE)
    listener_classes: list[str] = []
    for py_file in folder.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        code = py_file.read_text(encoding="utf-8")
        listener_classes.extend(class_pattern.findall(code))
    return listener_classes


def update_domain_listener_registration(domain: str, listener_classes: list[str]) -> None:
    domain_path = FEATURES_DIR / domain
    init_file = domain_path / "__init__.py"
    domain_class = to_pascal_case(domain)

    if not listener_classes:
        return

    if len(listener_classes) == 1:
        listener_tuple = f"({listener_classes[0]},)"
    else:
        listener_tuple = "(" + ", ".join(listener_classes) + ")"

    import_lines = "\n".join(
        f"            {listener_class}," for listener_class in listener_classes
    )
    content = (
        f"from app.features.{domain}.presentation.routes import {domain}_router\n"
        "from app.core.base_domain import BaseDomain\n\n\n"
        f"class {domain_class}Domain(BaseDomain):\n"
        f"    router = {domain}_router\n\n"
        "    def register_listeners(self):\n"
        f"        from app.features.{domain}.domain.listeners import (\n"
        f"{import_lines}\n"
        "        )\n\n"
        f"        self.listener_classes = {listener_tuple}\n"
        "        super().register_listeners()\n"
    )
    init_file.write_text(content, encoding="utf-8")


def create_domain(domain: str, force: bool = False) -> Path:
    domain_path = FEATURES_DIR / domain
    if domain_path.exists() and any(domain_path.iterdir()) and not force:
        raise FileExistsError(
            f"Domain '{domain}' already exists at {domain_path}. Use --force to overwrite files."
        )

    domain_class = to_pascal_case(domain)
    templates = render_templates(domain=domain, domain_class=domain_class)

    folders_to_init = [
        domain_path,
        domain_path / "data",
        domain_path / "data" / "repositories",
        domain_path / "domain",
        domain_path / "domain" / "entities",
        domain_path / "domain" / "repositories",
        domain_path / "domain" / "services",
        domain_path / "domain" / "usecases",
        domain_path / "presentation",
        domain_path / "presentation" / "routes",
        domain_path / "presentation" / "schema",
    ]

    for folder in folders_to_init:
        folder.mkdir(parents=True, exist_ok=True)
        init_file = folder / "__init__.py"
        if not init_file.exists():
            init_file.write_text("", encoding="utf-8")

    for relative_path, content in templates.items():
        target_file = domain_path / relative_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(content, encoding="utf-8")

    for folder in folders_to_init:
        refresh_folder_init(folder)

    # Restore authored package entry points after generated __init__ exports.
    for relative_path, content in templates.items():
        if Path(relative_path).name == "__init__.py":
            (domain_path / relative_path).write_text(content, encoding="utf-8")

    return domain_path


def create_model(domain: str, model: str, force: bool = False) -> Path:
    domain_path = FEATURES_DIR / domain
    if not domain_path.exists() or not domain_path.is_dir():
        raise FileNotFoundError(
            f"Domain '{domain}' does not exist at {domain_path}. Create the domain first."
        )

    domain_entities = domain_path / "domain" / "entities"
    domain_entities.mkdir(parents=True, exist_ok=True)

    init_file = domain_entities / "__init__.py"
    if not init_file.exists():
        init_file.write_text("__all__ = []\n", encoding="utf-8")

    model_class = to_pascal_case(model)
    templates = render_model_templates(domain=domain, model=model, model_class=model_class)

    entity_file = domain_path / f"domain/entities/{model}.py"

    if entity_file.exists() and not force:
        raise FileExistsError(
            f"Model files already exist for '{model}' in domain '{domain}'. "
            "Use --force to overwrite."
        )

    for relative_path, content in templates.items():
        target_file = domain_path / relative_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(content, encoding="utf-8")

    refresh_folder_init(domain_entities)

    return entity_file


def create_listener(
    domain: str,
    listener: str,
    event_import_path: str = "app.core.event_bus:BaseEvent",
    force: bool = False,
) -> Path:
    domain_path = FEATURES_DIR / domain
    if not domain_path.exists() or not domain_path.is_dir():
        raise FileNotFoundError(
            f"Domain '{domain}' does not exist at {domain_path}. Create the domain first."
        )

    listeners_dir = domain_path / "domain" / "listeners"
    listeners_dir.mkdir(parents=True, exist_ok=True)
    init_file = listeners_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("__all__ = []\n", encoding="utf-8")

    event_import, event_class = parse_event_import(event_import_path)
    class_name = listener_class_name(listener)
    templates = render_listener_templates(
        listener=listener,
        listener_class=class_name,
        event_import=event_import,
        event_class=event_class,
    )

    listener_file = domain_path / f"domain/listeners/{listener}.py"
    if listener_file.exists() and not force:
        raise FileExistsError(
            f"Listener file already exists for '{listener}' in domain '{domain}'. "
            "Use --force to overwrite."
        )

    for relative_path, content in templates.items():
        target_file = domain_path / relative_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(content, encoding="utf-8")

    refresh_folder_init(listeners_dir)
    update_domain_listener_registration(domain, listener_classes_in(listeners_dir))

    return listener_file
