import importlib
import pkgutil
from typing import TYPE_CHECKING

import models.clients

if TYPE_CHECKING:
    from collections.abc import Callable

    from models.base import BaseLLM

LLM_REGISTRY: dict[str, type[BaseLLM]] = {}


# define a decorator to register LLM classes
def register_llm(name: str) -> Callable[[type[BaseLLM]], type[BaseLLM]]:
    """Register an LLM class with the registry using a decorator."""

    def decorator(cls: type[BaseLLM]) -> type[BaseLLM]:
        LLM_REGISTRY[name] = cls
        return cls

    return decorator


# provide function to get a llm by registered name
def get_llm(name: str) -> type[BaseLLM]:
    """Get an LLM class from the registry."""
    try:
        return LLM_REGISTRY[name]
    except KeyError as e:
        available = ", ".join(LLM_REGISTRY.keys())
        msg = f"Unknown LLM provider '{name}'. Available providers: {available}"
        raise ValueError(msg) from e


def discover_clients() -> None:
    """Automatically discover LLM client classes in the models/clients folder."""
    for module_info in pkgutil.iter_modules(models.clients.__path__):
        importlib.import_module(f"models.clients.{module_info.name}")
