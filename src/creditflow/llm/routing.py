from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel

from creditflow.core.errors import ProviderError
from creditflow.llm.providers.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class ProviderCapabilities:
    structured_outputs: bool
    function_calling: bool
    approved_for_sensitive_data: bool


@dataclass(frozen=True)
class ProviderRoute:
    provider: LLMProvider
    capabilities: ProviderCapabilities


class CapabilityRouter:
    """Policy-based routing; retries only capability-compatible, approved providers."""

    def __init__(self, routes: list[ProviderRoute], *, max_attempts: int = 2) -> None:
        self.routes = routes
        self.max_attempts = max_attempts

    async def structured(
        self,
        *,
        instructions: str,
        input_text: str,
        output_type: type[T],
        tools: list[dict[str, object]] | None = None,
    ) -> T:
        eligible = [
            route
            for route in self.routes
            if route.capabilities.structured_outputs
            and route.capabilities.approved_for_sensitive_data
            and (not tools or route.capabilities.function_calling)
        ]
        failures: list[str] = []
        for route in eligible[: self.max_attempts]:
            try:
                return await route.provider.structured(
                    instructions=instructions,
                    input_text=input_text,
                    output_type=output_type,
                    tools=tools,
                )
            except ProviderError as exc:
                failures.append(f"{route.provider.name}:{exc.code}")
        raise ProviderError(
            "all approved compatible providers failed", details={"attempts": failures}
        )
