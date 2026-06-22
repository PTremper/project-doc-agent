from typing import TYPE_CHECKING

from openai import OpenAI

if TYPE_CHECKING:
    from openai.types.chat import (
        ChatCompletionDeveloperMessageParam,
        ChatCompletionUserMessageParam,
    )

from models.base import BaseLLM
from models.registry import register_llm


@register_llm("lmstudio")
class LMStudioLLM(BaseLLM):
    """A wrapper around the LMStudio client for generating responses from a local model."""

    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str = "dummy",
    ) -> None:
        """Initialize the LMStudioLLM with the given model and base URL."""
        self.client = OpenAI(api_key=api_key, base_url=base_url)

        self.model = model

    def build_prompt(
        self,
        system_prompt: str,
        context: str,
    ) -> list[ChatCompletionDeveloperMessageParam | ChatCompletionUserMessageParam]:

        system_prompt_dict: ChatCompletionDeveloperMessageParam = {
            "role": "developer",
            "content": system_prompt,
        }
        user_message_dict: ChatCompletionUserMessageParam = {
            "role": "user",
            "content": context,
        }

        return [system_prompt_dict, user_message_dict]

    def generate(
        self,
        messages: list[ChatCompletionDeveloperMessageParam | ChatCompletionUserMessageParam],
        max_tokens: int | None = None,
        temperature: float = 0.0,
    ) -> str:
        """Generate a response of the LLM based on the prompt."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            # temperature=temperature,
            max_tokens=max_tokens,
        )

        # check if this is the way to do this
        answer = response.choices[0].message.content
        if answer is None:
            return ""
        return answer

    def close_client(self) -> None:
        """Close the client."""
        self.client.close()
