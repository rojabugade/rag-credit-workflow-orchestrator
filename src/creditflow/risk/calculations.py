from collections.abc import Callable
from decimal import ROUND_HALF_EVEN, Decimal

from creditflow.schemas.underwriting import MetricResult

Q = Decimal("0.0001")


def _ratio(
    code: str,
    formula: str,
    numerator_name: str,
    numerator: Decimal | None,
    denominator_name: str,
    denominator: Decimal | None,
    source_ids: list[str],
) -> MetricResult:
    missing = [
        name
        for name, value in ((numerator_name, numerator), (denominator_name, denominator))
        if value is None
    ]
    if missing:
        return MetricResult(
            code=code,
            formula=formula,
            inputs={},
            source_ids=source_ids,
            result=None,
            validation_status="MISSING_INPUT",
            missing_inputs=missing,
        )
    assert numerator is not None and denominator is not None
    if denominator == 0:
        return MetricResult(
            code=code,
            formula=formula,
            inputs={numerator_name: numerator, denominator_name: denominator},
            source_ids=source_ids,
            result=None,
            validation_status="INVALID_DENOMINATOR",
            missing_inputs=[],
        )
    return MetricResult(
        code=code,
        formula=formula,
        inputs={numerator_name: numerator, denominator_name: denominator},
        source_ids=source_ids,
        result=(numerator / denominator).quantize(Q, rounding=ROUND_HALF_EVEN),
        validation_status="VALID",
    )


def calculate_debt_service_coverage_ratio(
    net_operating_income: Decimal | None, debt_service: Decimal | None, source_ids: list[str]
) -> MetricResult:
    return _ratio(
        "DSCR",
        "net_operating_income / annual_debt_service",
        "net_operating_income",
        net_operating_income,
        "annual_debt_service",
        debt_service,
        source_ids,
    )


def calculate_current_ratio(
    current_assets: Decimal | None, current_liabilities: Decimal | None, source_ids: list[str]
) -> MetricResult:
    return _ratio(
        "CURRENT_RATIO",
        "current_assets / current_liabilities",
        "current_assets",
        current_assets,
        "current_liabilities",
        current_liabilities,
        source_ids,
    )


def calculate_debt_to_equity(
    total_debt: Decimal | None, total_equity: Decimal | None, source_ids: list[str]
) -> MetricResult:
    return _ratio(
        "DEBT_TO_EQUITY",
        "total_debt / total_equity",
        "total_debt",
        total_debt,
        "total_equity",
        total_equity,
        source_ids,
    )


def calculate_loan_to_value(
    loan_amount: Decimal | None, collateral_value: Decimal | None, source_ids: list[str]
) -> MetricResult:
    return _ratio(
        "LTV",
        "loan_amount / collateral_value",
        "loan_amount",
        loan_amount,
        "collateral_value",
        collateral_value,
        source_ids,
    )


def calculate_operating_margin(
    operating_income: Decimal | None, revenue: Decimal | None, source_ids: list[str]
) -> MetricResult:
    return _ratio(
        "OPERATING_MARGIN",
        "operating_income / revenue",
        "operating_income",
        operating_income,
        "revenue",
        revenue,
        source_ids,
    )


CALCULATION_TOOLS: dict[str, Callable[..., MetricResult]] = {
    "calculate_debt_service_coverage_ratio": calculate_debt_service_coverage_ratio,
    "calculate_current_ratio": calculate_current_ratio,
    "calculate_debt_to_equity": calculate_debt_to_equity,
    "calculate_loan_to_value": calculate_loan_to_value,
    "calculate_operating_margin": calculate_operating_margin,
}
