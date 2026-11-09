import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol, TypeVar, cast

from litellm.router import Router
from pydantic import BaseModel, ValidationError

from creditflow.core.config import Settings
from creditflow.core.errors import ProviderError
from creditflow.llm.token_budget import TokenBudget, enforce_token_budget

T = TypeVar("T", bound=BaseModel)


class TaskComplexity(StrEnum):
    SIMPLE = "SIMPLE"
    COMPLEX = "COMPLEX"


class AsyncLiteLLMRouter(Protocol):
    async def acompletion(
        self, model: str, messages: list[dict[str, str]], **kwargs: object
    ) -> Any: ...


@dataclass(frozen=True)
class RoutedUsage:
    provider_model: str
    input_tokens: int
    output_tokens: int


class LiteLLMStructuredRouter:
    """Validated application boundary around LiteLLM's real async Router."""

    def __init__(
        self,
        router: AsyncLiteLLMRouter,
        *,
        simple_alias: str,
        complex_alias: str,
        budget: TokenBudget | None = None,
    ) -> None:
        self._router = router
        self._aliases = {
            TaskComplexity.SIMPLE: simple_alias,
            TaskComplexity.COMPLEX: complex_alias,
        }
        self._budget = budget or TokenBudget(128_000, 4096, 512)

    async def structured(
        self,
        *,
        tenant_id: str,
        instructions: str,
        evidence_sections: list[str],
        output_type: type[T],
        complexity: TaskComplexity,
        sensitive: bool = True,
    ) -> tuple[T, RoutedUsage]:
        selected = enforce_token_budget(
            evidence_sections,
            self._budget,
            preserve_prefix_sections=min(1, len(evidence_sections)),
        )
        schema = output_type.model_json_schema()
        try:
            response = await self._router.acompletion(
                model=self._aliases[complexity],
                messages=[
                    {"role": "system", "content": instructions},
                    {"role": "user", "content": "\n\n".join(selected)},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": output_type.__name__,
                        "strict": True,
                        "schema": schema,
                    },
                },
                metadata={"tenant_id": tenant_id, "sensitive": sensitive},
                caching=not sensitive,
            )
            content = response.choices[0].message.content
            if not isinstance(content, str):
                raise ProviderError("LiteLLM returned no structured text")
            result = output_type.model_validate(json.loads(content))
            usage_object = getattr(response, "usage", None)
            usage = RoutedUsage(
                provider_model=str(getattr(response, "model", self._aliases[complexity])),
                input_tokens=int(getattr(usage_object, "prompt_tokens", 0) or 0),
                output_tokens=int(getattr(usage_object, "completion_tokens", 0) or 0),
            )
            return result, usage
        except ProviderError:
            raise
        except (ValidationError, json.JSONDecodeError, IndexError, AttributeError) as exc:
            raise ProviderError("LiteLLM response failed strict schema validation") from exc
        except Exception as exc:
            raise ProviderError("LiteLLM routing request failed") from exc


def build_litellm_router(settings: Settings) -> LiteLLMStructuredRouter:
    model_list: list[dict[str, Any]] = []
    if settings.openai_api_key:
        deployment = {
            "litellm_params": {
                "model": f"openai/{settings.openai_model}",
                "api_key": settings.openai_api_key,
            }
        }
        model_list.extend(
            [
                {"model_name": settings.llm_simple_alias, **deployment},
                {"model_name": settings.llm_complex_alias, **deployment},
            ]
        )
    if settings.anthropic_api_key:
        model_list.append(
            {
                "model_name": settings.llm_complex_alias,
                "litellm_params": {
                    "model": f"anthropic/{settings.anthropic_model}",
                    "api_key": settings.anthropic_api_key,
                },
            }
        )
    if settings.bedrock_model:
        model_list.append(
            {
                "model_name": settings.llm_complex_alias,
                "litellm_params": {"model": f"bedrock/{settings.bedrock_model}"},
            }
        )
    if not model_list:
        raise ProviderError("no LiteLLM deployments are configured")
    router = Router(
        model_list=cast("Any", model_list),
        routing_strategy="cost-based-routing",
        num_retries=settings.workflow_max_retries,
        timeout=settings.request_timeout_seconds,
        fallbacks=[{settings.llm_complex_alias: [settings.llm_simple_alias]}],
        cache_responses=settings.sensitive_llm_cache_enabled,
        redis_url=settings.redis_url if settings.sensitive_llm_cache_enabled else None,
        enable_pre_call_checks=True,
    )
    return LiteLLMStructuredRouter(
        cast("AsyncLiteLLMRouter", router),
        simple_alias=settings.llm_simple_alias,
        complex_alias=settings.llm_complex_alias,
    )
