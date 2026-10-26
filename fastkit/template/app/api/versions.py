"""API version vocabulary.

Deliberately a leaf module: it imports nothing from the rest of the app, so anything
(including `app.core`) can read the prefixes without pulling in the feature packages
that the version packages themselves assemble.
"""

from enum import StrEnum


class ApiVersion(StrEnum):
    V1 = "v1"

    @property
    def prefix(self) -> str:
        """Mount point for every route in this version, e.g. `/v1`."""
        return f"/{self.value}"

    @property
    def docs_url(self) -> str:
        return f"{self.prefix}/docs"

    @property
    def openapi_url(self) -> str:
        return f"{self.prefix}/openapi.json"


# The version whose docs are served and which new clients should target.
CURRENT_API_VERSION = ApiVersion.V1
