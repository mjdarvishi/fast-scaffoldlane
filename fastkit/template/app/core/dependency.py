"""
Dependency Injection System with Auto-Discovery

This module provides a decorator-based dependency injection system with automatic class discovery.

Setup (in main.py):
    from app.core.dependency import injector

    # Scan and load all @injectable classes at startup
    injector.scan_and_load_all("app")

Usage:
    1. Decorate your classes with @injectable() or @provides(Interface)
    2. Use injector.get(ClassName) or injector[ClassName]() to retrieve instances
    3. All classes are auto-loaded at startup - no imports or registration needed!

Example:
    # In your repository implementation
    @provides(UserRepository)
    class UserRepositoryImpl(UserRepository):
        pass

    # In your use case (dependencies auto-injected)
    @injectable()
    class LoginUseCase:
        def __init__(self, repo: UserRepository):
            self.repo = repo

    # In your route/controller
    def my_route():
        usecase = injector.get(LoginUseCase)
        # or
        usecase = injector[LoginUseCase]()

The injector automatically scans the entire app module at startup.
No configuration files needed!
"""

from typing import Any, Type, TypeVar, Dict, Callable, Optional, get_type_hints, List
import inspect
import importlib
import pkgutil
from pathlib import Path
import sys

T = TypeVar("T")


class Injector:
    _factories: Dict[Type, Callable[[], object]] = {}
    _search_modules: List[str] = []
    _auto_discovered: set = set()
    _initialized = False

    @classmethod
    def register(cls, type_: Type[T], factory: Callable[[], T]):
        cls._factories[type_] = factory

    @classmethod
    def register_search_path(cls, module_path: str):
        """Register a module path for auto-discovery of injectable classes."""
        if module_path not in cls._search_modules:
            cls._search_modules.append(module_path)

    @classmethod
    def _initialize_default_paths(cls):
        """Initialize default search paths based on app structure."""
        if cls._initialized:
            return

        cls._initialized = True

        # Add common patterns for features
        try:
            import app.features

            features_path = Path(app.features.__file__).parent

            # Automatically discover all feature modules
            for feature_dir in features_path.iterdir():
                if feature_dir.is_dir() and not feature_dir.name.startswith("_"):
                    feature_name = feature_dir.name
                    # Register common paths in each feature
                    cls.register_search_path(f"app.features.{feature_name}.data.repositories")
                    cls.register_search_path(f"app.features.{feature_name}.domain.usecases")
        except Exception:
            pass

        # Register core paths
        cls.register_search_path("app.core")

    @classmethod
    def _try_auto_discover(cls, type_: Type[T]) -> bool:
        """
        Attempt to auto-discover and import the module containing the requested type.
        Returns True if discovery was successful.
        """
        # Initialize default paths if needed
        cls._initialize_default_paths()

        type_name = getattr(type_, "__name__", None)
        if type_name is None:
            return False

        # Avoid infinite recursion - but only if we're currently discovering this type
        if type_name in cls._auto_discovered:
            return False

        # Mark as being discovered (temporarily)
        cls._auto_discovered.add(type_name)

        try:
            # Search in registered module paths
            for module_path in cls._search_modules:
                try:
                    # Try to import the module
                    module = importlib.import_module(module_path)

                    if not hasattr(module, "__file__") or module.__file__ is None:
                        continue

                    module_dir = Path(module.__file__).parent

                    # Walk through all Python files in the module
                    for finder, name, ispkg in pkgutil.walk_packages(
                        [str(module_dir)], f"{module_path}."
                    ):
                        try:
                            # Import the module - this triggers @injectable/@provides decorators
                            importlib.import_module(name)

                            # Check if the type is now registered
                            if type_ in cls._factories:
                                return True
                        except Exception as e:
                            # Skip modules that fail to import
                            import traceback

                            # Uncomment for debugging
                            # print(f"Failed to import {name}: {e}")
                            # traceback.print_exc()
                            continue

                except Exception as e:
                    # Uncomment for debugging
                    # print(f"Failed to scan {module_path}: {e}")
                    continue

            return False
        finally:
            # Remove from discovered set if we didn't find it, so we can try again later
            if type_ not in cls._factories:
                cls._auto_discovered.discard(type_name)

    @classmethod
    def get(cls, type_: Type[T]) -> T:
        # Try to get from registered factories
        if type_ in cls._factories:
            return cls._factories[type_]()

        # Try auto-discovery
        if cls._try_auto_discover(type_):
            if type_ in cls._factories:
                return cls._factories[type_]()

        type_name = getattr(type_, "__name__", repr(type_))
        raise ValueError(f"No registered factory for type: {type_name}")

    @classmethod
    def clear(cls):
        cls._factories.clear()
        cls._auto_discovered.clear()
        cls._initialized = False

    @classmethod
    def scan_and_load_all(cls, base_module: str = "app"):
        """
        Eagerly scan and load all Python modules in the project to register @injectable classes.
        This should be called at application startup.

        Args:
            base_module: The base module to scan (default: "app")
        """
        try:
            module = importlib.import_module(base_module)

            if not hasattr(module, "__file__") or module.__file__ is None:
                return

            module_path = Path(module.__file__).parent

            # Recursively walk through all packages and modules
            for finder, name, ispkg in pkgutil.walk_packages([str(module_path)], f"{base_module}."):
                try:
                    # Skip test files, __pycache__, and certain patterns
                    if any(
                        part.startswith("__pycache__") or part == "tests"
                        for part in name.split(".")
                    ):
                        continue

                    # Import the module to trigger decorators
                    importlib.import_module(name)
                except Exception as e:
                    # Print debug info for import failures
                    import traceback

                    print(f"Warning: Failed to import {name}: {e}")
                    traceback.print_exc()
                    pass

            print(f"Dependency injection: Loaded {len(cls._factories)} injectable classes")
        except Exception as e:
            print(f"Warning: Failed to scan modules: {e}")

    def __getitem__(self, type_: Type[T]) -> Callable[[], T]:
        return lambda: self.get(type_)


injector = Injector()


def injectable(interface: Optional[Type] = None, singleton: bool = False):
    """
    Decorator to automatically register a class with the injector.

    Args:
        interface: The interface/base class this implementation provides.
                   If None, registers the class itself.
        singleton: If True, creates a single instance that is reused.

    Usage:
        @injectable()
        class MyService:
            pass

        @injectable(interface=MyRepository)
        class MyRepositoryImpl(MyRepository):
            pass
    """

    def decorator(cls: Type[T]) -> Type[T]:
        _instance = None

        def factory() -> T:
            nonlocal _instance

            # If singleton and already created, return existing instance
            if singleton and _instance is not None:
                return _instance

            # Get constructor parameters
            try:
                sig = inspect.signature(cls.__init__)
                params = sig.parameters
                type_hints = get_type_hints(cls.__init__)

                # Build dependencies
                kwargs = {}
                for param_name, param in params.items():
                    if param_name == "self" or param.kind in (
                        inspect.Parameter.VAR_POSITIONAL,
                        inspect.Parameter.VAR_KEYWORD,
                    ):
                        continue

                    # Try to get the type annotation
                    if param.annotation != inspect.Parameter.empty:
                        param_type = type_hints.get(param_name, param.annotation)
                        if param_type is Any:
                            continue
                        try:
                            kwargs[param_name] = injector.get(param_type)
                        except ValueError:
                            # If dependency not found and no default, raise error
                            if param.default == inspect.Parameter.empty:
                                param_type_name = getattr(param_type, "__name__", repr(param_type))
                                raise ValueError(
                                    f"Cannot resolve dependency '{param_name}: {param_type_name}' "
                                    f"for {cls.__name__}. Make sure it's registered with @injectable."
                                )

                instance = cls(**kwargs)

                if singleton:
                    _instance = instance

                return instance
            except Exception as e:
                # Fallback to no-args constructor
                try:
                    instance = cls()
                    if singleton:
                        _instance = instance
                    return instance
                except:
                    raise e

        # Register with interface or the class itself
        registration_type = interface if interface is not None else cls
        injector.register(registration_type, factory)

        return cls

    return decorator


def provides(interface: Type[T]):
    """
    Alias for injectable with interface parameter for better readability.

    Usage:
        @provides(MyRepository)
        class MyRepositoryImpl(MyRepository):
            pass
    """
    return injectable(interface=interface)
