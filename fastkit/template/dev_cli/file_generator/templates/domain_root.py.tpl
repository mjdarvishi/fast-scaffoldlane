from app.features.{domain}.presentation.routes import {domain}_router
from app.core.base_domain import BaseDomain


class {domain_class}Domain(BaseDomain):
    router = {domain}_router
    listener_classes = ()
