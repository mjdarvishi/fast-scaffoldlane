from collections.abc import Iterable
from typing import Any


class BaseDomain:
    """A feature package's entry point.

    A domain exposes its router and its listeners; it does not mount itself. Which
    versions expose a domain is decided in `app.api.<version>`, so a feature can be
    added to one version without being added to another.
    """

    router: Any = None
    listener_classes: Iterable[type] = ()

    def __init__(self, *args, **kwargs):
        self._listener_instances = []
        super().__init__(*args, **kwargs)

    @property
    def routes(self) -> Any:
        # Backward-compatible alias.
        return self.router

    @property
    def listeners(self) -> Iterable[type]:
        # Backward-compatible alias.
        return self.listener_classes

    def register_listeners(self):
        # Instantiate listener classes so they auto-register in their __init__.
        self._listener_instances = [listener() for listener in self.listener_classes]
