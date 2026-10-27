"""Local email and password authentication feature."""

from app.core.base_domain import BaseDomain
from app.features.auth.presentation.routes.auth import auth_router


class AuthDomain(BaseDomain):
    router = auth_router
    listener_classes = ()
