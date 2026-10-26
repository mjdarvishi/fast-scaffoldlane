from app.features.{domain}.presentation.routes import main_router
from app.core.base_domain import BaseDomain


class {domain_class}Domain(BaseDomain):
    router = main_router
    listener_classes = ()
