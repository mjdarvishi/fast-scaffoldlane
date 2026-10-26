"""Build-time identity of this service, read from pyproject.toml's `[project]` table.

Distinct from `app.api.versions`, which is about the versions of the HTTP surface: the
value here is the release of the running code, not a path segment.
"""

import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Any

PYPROJECT_PATH = Path(__file__).resolve().parents[2] / "pyproject.toml"


def _project_table() -> dict[str, Any]:
    # Deliberately uncached: the accessors below own the caching, so clearing one of
    # them is enough to pick up a different PYPROJECT_PATH (as the tests do).
    with PYPROJECT_PATH.open("rb") as pyproject_file:
        return dict(tomllib.load(pyproject_file)["project"])


@lru_cache
def get_app_version() -> str:
    return str(_project_table()["version"])


@lru_cache
def get_app_name() -> str:
    return str(_project_table()["name"])


@lru_cache
def get_app_description() -> str:
    return str(_project_table().get("description", ""))
