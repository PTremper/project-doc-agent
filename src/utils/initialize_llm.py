from typing import TYPE_CHECKING

from src.models.registry import get_llm

if TYPE_CHECKING:
    from src.models.base import BaseLLM


def initialize_llm(config: dict[str, dict[str, str]], llm_task: str) -> BaseLLM:
    """Initialize the LLM for the given task using the given configuration.

    This function wraps checking all the config entries and error handling.
    """
    llm_config = config.get(f"{llm_task}")
    if llm_config is None:
        msg = f"{llm_task} is not configured"
        raise KeyError(msg)
    if (provider := llm_config.get("provider")) is None:
        msg = f"{llm_task}provider is not configured"
        raise KeyError(msg)
    if (model := llm_config.get("model")) is None:
        msg = f"{llm_task} model is not configured"
        raise KeyError(msg)
    if (base_url := llm_config.get("base_url")) is None:
        msg = f"{llm_task} base_url is not configured"
        raise KeyError(msg)
    if (api_key := llm_config.get("api_key")) is None:
        msg = f"{llm_task} api_key is not configured"
        raise KeyError(msg)
    llm_class = get_llm(provider)
    return llm_class(model=model, base_url=base_url, api_key=api_key)
