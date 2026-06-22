from abc import ABC, abstractmethod
from typing import Any


class BaseLLM(ABC):
    """Base class for LLMs, enforcing a generate method."""

    @abstractmethod
    def __init__(self, model: str, base_url: str, api_key: str = "") -> None:
        """Initialize the LLM with the given model, base URL, and API key."""

    @abstractmethod
    def build_prompt(self, system_prompt: str, context: str) -> list[Any]:
        """Construct the prompt for the LLM."""

    @abstractmethod
    def generate(
        self,
        messages: list[Any],
        max_tokens: int | None = None,
        temperature: float = 0.0,
    ) -> str:
        """Generate a LLM response."""

    @abstractmethod
    def close_client(self) -> None:
        """Close the client."""
