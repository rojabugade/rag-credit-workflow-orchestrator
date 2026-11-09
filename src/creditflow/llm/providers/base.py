from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def structured(
        self,
        *,
        instructions: str,
        input_text: str,
        output_type: type[T],
        tools: list[dict[str, object]] | None = None,
    ) -> T:
        """Return a schema-validated result or raise a structured provider error."""
