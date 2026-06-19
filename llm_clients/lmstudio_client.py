from typing import TYPE_CHECKING

from openai import OpenAI

if TYPE_CHECKING:
    from openai.types.chat import (
        ChatCompletionDeveloperMessageParam,
        ChatCompletionUserMessageParam,
    )


class LMStudioLLM:
    """A wrapper around the LMStudio client for generating responses from a local model."""

    def __init__(
        self,
        model: str,
        base_url: str = "http://127.0.0.1:1234/v1",
        api_key: str = "dummy",
    ) -> None:
        """Initialize the LMStudioLLM with the given model and base URL."""
        self.client = OpenAI(api_key=api_key, base_url=base_url)

        self.model = model

    def build_prompt(
        self,
        system_prompt: str,
        content: str,
    ) -> list[ChatCompletionDeveloperMessageParam | ChatCompletionUserMessageParam]:

        system_prompt_dict: ChatCompletionDeveloperMessageParam = {
            "role": "developer",
            "content": system_prompt,
        }
        user_message_dict: ChatCompletionUserMessageParam = {
            "role": "user",
            "content": content,
        }

        return [system_prompt_dict, user_message_dict]

    def generate(
        self,
        messages: list[ChatCompletionDeveloperMessageParam | ChatCompletionUserMessageParam],
        # temperature: float = 0.0,
        max_tokens: int | None = None,
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
