"""OpenAPI schema and Swagger UI helpers."""

from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from app.api.versions import CURRENT_API_VERSION
from app.core.project import get_app_description, get_app_name, get_app_version


def custom_swagger_ui():
    """Return the standard Swagger UI for the versioned OpenAPI schema."""
    return get_swagger_ui_html(
        openapi_url=CURRENT_API_VERSION.openapi_url,
        title=f"{get_app_name()} API Docs",
    )


def custom_openapi(app):
    """Build the API schema with the common JWT bearer scheme."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=get_app_name(),
        version=get_app_version(),
        description=get_app_description(),
        routes=app.routes,
        servers=app.servers,
    )
    openapi_schema.setdefault("components", {})["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    for path in openapi_schema["paths"].values():
        for operation in path.values():
            if isinstance(operation, dict):
                operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema
