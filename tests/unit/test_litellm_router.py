import json
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import BaseModel, ConfigDict

from creditflow.llm.litellm_router import LiteLLMStructuredRouter, TaskComplexity


class Result(BaseModel):
    model_config = ConfigDict(extra="forbid")
    finding: str


class FakeRouter:
    def __init__(self) -> None:
        self.arguments: dict[str, Any] = {}

    async def acompletion(
        self, model: str, messages: list[dict[str, str]], **kwargs: object
    ) -> Any:
        self.arguments = {"model": model, "messages": messages, **kwargs}
        return SimpleNamespace(
            model="synthetic-model",
            choices=[
                SimpleNamespace(message=SimpleNamespace(content=json.dumps({"finding": "ok"})))
            ],
            usage=SimpleNamespace(prompt_tokens=12, completion_tokens=3),
        )


@pytest.mark.asyncio
async def test_litellm_router_uses_alias_schema_and_disables_sensitive_cache() -> None:
    fake = FakeRouter()
    router = LiteLLMStructuredRouter(
        fake,
        simple_alias="credit-simple",
        complex_alias="credit-complex",
    )
    result, usage = await router.structured(
        tenant_id="tenant-1",
        instructions="Return only grounded findings.",
        evidence_sections=["[SOURCE synthetic:1] evidence [/SOURCE]"],
        output_type=Result,
        complexity=TaskComplexity.COMPLEX,
        sensitive=True,
    )
    assert result.finding == "ok"
    assert usage.input_tokens == 12
    assert fake.arguments["model"] == "credit-complex"
    assert fake.arguments["caching"] is False
    assert fake.arguments["response_format"]["type"] == "json_schema"
