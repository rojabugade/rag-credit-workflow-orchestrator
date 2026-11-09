from typing import Any, TypeVar, cast

from openai import AsyncOpenAI
from pydantic import BaseModel

from creditflow.core.errors import ProviderError
from creditflow.llm.providers.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class OpenAIResponsesProvider(LLMProvider):
    name = "openai-responses"

    def __init__(self, api_key: str, model: str, timeout: float = 30.0) -> None:
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout, max_retries=2)
        self._model = model

    async def structured(
        self,
        *,
        instructions: str,
        input_text: str,
        output_type: type[T],
        tools: list[dict[str, object]] | None = None,
    ) -> T:
        try:
            response = await self._client.responses.parse(
                model=self._model,
                instructions=instructions,
                input=input_text,
                text_format=output_type,
                tools=cast("Any", tools or []),
                max_output_tokens=4096,
            )
        except Exception as exc:
            raise ProviderError("OpenAI Responses API call failed") from exc
        if response.status != "completed":
            raise ProviderError("LLM response was incomplete", details={"status": response.status})
        if response.output_parsed is None:
            refusal = next(
                (
                    part.refusal
                    for item in response.output
                    if item.type == "message"
                    for part in item.content
                    if part.type == "refusal"
                ),
                None,
            )
            raise ProviderError(
                "LLM refused or returned malformed output",
                details={"refusal": refusal or "unknown"},
            )
        return output_type.model_validate(response.output_parsed)
