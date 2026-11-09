from decimal import Decimal

import pytest

from creditflow.core.errors import ProviderError
from creditflow.llm.cost_tracker import ModelPricing, estimate_cost
from creditflow.llm.token_budget import TokenBudget, enforce_token_budget


def test_cost_estimation_uses_decimal() -> None:
    result = estimate_cost(
        1_000_000,
        500_000,
        ModelPricing(Decimal("1.00"), Decimal("2.00")),
    )
    assert result == Decimal("2.000000")


def test_token_budget_preserves_mandatory_evidence_or_fails() -> None:
    with pytest.raises(ProviderError):
        enforce_token_budget(
            ["x" * 1000],
            TokenBudget(
                max_context_tokens=200,
                reserved_output_tokens=20,
                safety_margin_tokens=0,
            ),
        )
