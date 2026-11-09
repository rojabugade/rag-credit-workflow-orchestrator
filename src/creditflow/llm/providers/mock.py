import json
from typing import TypeVar

from pydantic import BaseModel

from creditflow.core.errors import ProviderError
from creditflow.llm.providers.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class DeterministicMockProvider(LLMProvider):
    """Offline provider: input must contain the exact expected JSON object."""

    name = "deterministic-mock"

    async def structured(
        self,
        *,
        instructions: str,
        input_text: str,
        output_type: type[T],
        tools: list[dict[str, object]] | None = None,
    ) -> T:
        del instructions, tools
        try:
            return output_type.model_validate(json.loads(input_text))
        except (json.JSONDecodeError, ValueError) as exc:
            raise ProviderError("mock response did not satisfy the requested schema") from exc
