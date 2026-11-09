from decimal import Decimal

from creditflow.risk.calculations import (
    calculate_current_ratio,
    calculate_debt_service_coverage_ratio,
    calculate_debt_to_equity,
    calculate_loan_to_value,
    calculate_operating_margin,
)
from creditflow.workflows.agents.intake import decimal_fact
from creditflow.workflows.state import UnderwritingState


def financial_analysis(state: UnderwritingState) -> dict[str, object]:
    facts = state.get("facts", {})
    sources = state.get("source_ids", [])
    metrics = [
        calculate_debt_service_coverage_ratio(
            decimal_fact(facts, "net_operating_income"),
            decimal_fact(facts, "annual_debt_service"),
            sources,
        ),
        calculate_current_ratio(
            decimal_fact(facts, "current_assets"),
            decimal_fact(facts, "current_liabilities"),
            sources,
        ),
        calculate_debt_to_equity(
            decimal_fact(facts, "total_debt"), decimal_fact(facts, "total_equity"), sources
        ),
        calculate_loan_to_value(
            Decimal(state["requested_amount"]), decimal_fact(facts, "collateral_value"), sources
        ),
        calculate_operating_margin(
            decimal_fact(facts, "operating_income"), decimal_fact(facts, "revenue"), sources
        ),
    ]
    return {
        "financial_metrics": [metric.model_dump(mode="json") for metric in metrics],
        "financial_observations": [
            f"{metric.code}={metric.result}" for metric in metrics if metric.result is not None
        ],
    }
