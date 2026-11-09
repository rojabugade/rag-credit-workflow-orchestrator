from decimal import Decimal

from creditflow.risk.calculations import calculate_debt_service_coverage_ratio
from creditflow.risk.rules import evaluate_rules


def test_dscr_is_decimal_and_provenanced() -> None:
    metric = calculate_debt_service_coverage_ratio(Decimal("135000"), Decimal("100000"), ["doc:p4"])
    assert metric.result == Decimal("1.3500")
    assert metric.formula == "net_operating_income / annual_debt_service"
    assert metric.source_ids == ["doc:p4"]


def test_missing_input_escalates() -> None:
    metric = calculate_debt_service_coverage_ratio(None, Decimal("100000"), [])
    level, flags = evaluate_rules([metric], missing_documents=["income_statement"])
    assert level.value == "INSUFFICIENT_DATA"
    assert flags[0].code == "MISSING_INFORMATION"
