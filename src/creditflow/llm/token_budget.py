from dataclasses import dataclass

from creditflow.core.errors import ProviderError


@dataclass(frozen=True)
class TokenBudget:
    max_context_tokens: int
    reserved_output_tokens: int
    safety_margin_tokens: int = 256

    @property
    def available_input_tokens(self) -> int:
        available = (
            self.max_context_tokens - self.reserved_output_tokens - self.safety_margin_tokens
        )
        if available <= 0:
            raise ValueError("token budget leaves no room for input")
        return available


class HeuristicTokenEstimator:
    """Offline-safe estimate; provider-specific tokenizers can replace it."""

    def estimate(self, text: str) -> int:
        return max(1, (len(text) + 3) // 4)


def enforce_token_budget(
    sections: list[str],
    budget: TokenBudget,
    *,
    preserve_prefix_sections: int = 1,
    estimator: HeuristicTokenEstimator | None = None,
) -> list[str]:
    """Keep whole evidence sections and fail if mandatory evidence cannot fit."""
    counter = estimator or HeuristicTokenEstimator()
    limit = budget.available_input_tokens
    selected: list[str] = []
    used = 0
    for index, section in enumerate(sections):
        section_tokens = counter.estimate(section)
        if used + section_tokens > limit:
            if index < preserve_prefix_sections:
                raise ProviderError("mandatory evidence exceeds the configured token budget")
            continue
        selected.append(section)
        used += section_tokens
    return selected
