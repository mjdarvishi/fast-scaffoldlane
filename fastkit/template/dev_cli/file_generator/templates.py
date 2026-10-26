from importlib.resources import files
from pathlib import Path
from string import Formatter

DOMAIN_TEMPLATE_FILES = {
    "__init__.py": "domain_root.py.tpl",
    "data/dtos/{domain}.py": "data/dtos/domain_dto.py.tpl",
    "data/repositories/{domain}_repo.py": "data/repositories/domain_repo.py.tpl",
    "domain/entities/{domain}.py": "domain/entities/domain_entity.py.tpl",
    "domain/usecases/{domain}.py": "domain/usecases/domain_usecase.py.tpl",
    "presentation/routes/{domain}.py": "presentation/routes/domain_route.py.tpl",
    "presentation/policy/__init__.py": "presentation/policy/init.py.tpl",
    "presentation/routes/__init__.py": "presentation/routes/init.py.tpl",
    "presentation/schema/__init__.py": "presentation/schema/init.py.tpl",
}

MODEL_TEMPLATE_FILES = {
    "data/dtos/{model}.py": "data/dtos/model_dto.py.tpl",
    "domain/entities/{model}.py": "domain/entities/model_entity.py.tpl",
}

LISTENER_TEMPLATE_FILES = {
    "domain/listeners/{listener}.py": "domain/listeners/listener.py.tpl",
}


class SafeTemplateValues(dict[str, str]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def render_template_file(template_path: str, values: dict[str, str]) -> str:
    template = (
        files(__package__)
        .joinpath("templates")
        .joinpath(*Path(template_path).parts)
        .read_text(encoding="utf-8")
    )
    return Formatter().vformat(template, (), SafeTemplateValues(values))


def render_named_templates(
    template_files: dict[str, str],
    values: dict[str, str],
) -> dict[str, str]:
    safe_values = SafeTemplateValues(values)
    rendered: dict[str, str] = {}
    for relative_path_template, template_path in template_files.items():
        relative_path = Formatter().vformat(relative_path_template, (), safe_values)
        rendered[relative_path] = render_template_file(template_path, safe_values)
    return rendered


def render_templates(domain: str, domain_class: str) -> dict[str, str]:
    return render_named_templates(
        DOMAIN_TEMPLATE_FILES,
        {
            "domain": domain,
            "domain_class": domain_class,
        },
    )


def render_model_templates(domain: str, model: str, model_class: str) -> dict[str, str]:
    return render_named_templates(
        MODEL_TEMPLATE_FILES,
        {
            "domain": domain,
            "model": model,
            "model_class": model_class,
        },
    )


def render_listener_templates(
    listener: str,
    listener_class: str,
    event_import: str,
    event_class: str,
) -> dict[str, str]:
    return render_named_templates(
        LISTENER_TEMPLATE_FILES,
        {
            "listener": listener,
            "listener_class": listener_class,
            "event_import": event_import,
            "event_class": event_class,
        },
    )
