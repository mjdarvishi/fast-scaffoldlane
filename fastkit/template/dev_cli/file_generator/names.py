import re

DOMAIN_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def to_pascal_case(value: str) -> str:
    return "".join(part.capitalize() for part in value.split("_") if part)


def normalize_domain_name(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    if not DOMAIN_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Invalid domain name. Use letters, numbers, underscores, and start with a letter."
        )
    return normalized


def normalize_model_name(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    if not DOMAIN_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Invalid model name. Use letters, numbers, underscores, and start with a letter."
        )
    return normalized


def normalize_listener_name(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    if not DOMAIN_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Invalid listener name. Use letters, numbers, underscores, and start with a letter."
        )
    return normalized
