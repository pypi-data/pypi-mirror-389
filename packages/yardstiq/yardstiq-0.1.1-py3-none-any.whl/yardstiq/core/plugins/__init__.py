from typing import Dict, Type, Callable, List
from pathlib import Path

from ..interfaces import Provider, Backend, Benchmark, Dataset

from .local_provider import LocalProvider
from .installed_plugins import load_installed_plugins
from .local_project_plugins import load_project_plugins
from .local_manual_plugins import load_local_plugin

PROVIDER_REGISTRY: Dict[str, Provider] = {"local": LocalProvider()}


def provider(name: str) -> Callable:
    """
    DECORATOR (for packages): Registers a new Provider class.
    Used by external packages like 'yardstiq-scaleway', 'yardstiq-aqora' or 'yardstiq-quandela'.
    """

    def decorator(cls: Type[Provider]) -> Type[Provider]:
        if not issubclass(cls, Provider):
            raise TypeError(f"Class {cls.__name__} must inherit from Provider")

        if name in PROVIDER_REGISTRY:
            print(f"[Yardstiq] WARNING: Provider '{name}' is being redefined.")

        try:
            instance = cls(name)
            instance.name = name
            PROVIDER_REGISTRY[name] = instance
        except Exception as e:
            print(f"[Yardstiq] WARNING: Failed to instantiate provider '{name}': {e}")

        return cls

    return decorator


def backend(name: str) -> Callable:
    """
    DECORATOR (for local files): Registers a Backend class
    with the implicit 'local' provider.
    """

    def decorator(cls: Type[Backend]) -> Type[Backend]:
        if not issubclass(cls, Backend):
            raise TypeError(f"Class {cls.__name__} must inherit from Backend")

        localp: LocalProvider = PROVIDER_REGISTRY["local"]
        localp.add_backend(cls(localp, name, "0.1"), name)

        return cls

    return decorator


def benchmark(name: str) -> Callable:
    """
    DECORATOR (for local files): Registers a Benchmark class
    with the implicit 'local' provider.
    """

    def decorator(cls: Type[Benchmark]) -> Type[Benchmark]:
        if not issubclass(cls, Benchmark):
            raise TypeError(f"Class {cls.__name__} must inherit from Benchmark")

        localp: LocalProvider = PROVIDER_REGISTRY["local"]
        localp.add_benchmark(cls(localp, name, "0.1"), name)

        return cls

    return decorator


def dataset(name: str) -> Callable:
    """
    DECORATOR (for local files): Registers a Dataset class
    with the implicit 'local' provider.
    """

    def decorator(cls: Type[Dataset]) -> Type[Dataset]:
        if not issubclass(cls, Dataset):
            raise TypeError(f"Class {cls.__name__} must inherit from Dataset")

        localp: LocalProvider = PROVIDER_REGISTRY["local"]
        localp.add_dataset(cls(localp, name, "0.1"), name)

        return cls

    return decorator


_plugins_loaded = False


def load_all_plugins(local_files: List[Path] = None):
    """
    Orchestrates loading all plugins.
    This function simply executes the plugin files; the decorators
    do the work of registering themselves.
    """
    global _plugins_loaded
    if _plugins_loaded:
        return

    print("[Yardstiq] Initializing and loading provider plugins...")

    load_installed_plugins()

    load_project_plugins()

    if local_files and len(local_files) > 0:
        print(f"[Yardstiq] Loading {len(local_files)} local plugin(s) via --load...")

        for file_path in local_files:
            load_local_plugin(file_path)

    _plugins_loaded = True
