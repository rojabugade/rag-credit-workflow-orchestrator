from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from creditflow.schemas.underwriting import MetricResult, RiskFlag, RiskLevel


@dataclass(frozen=True)
class RiskThresholds:
    version: str = "synthetic-commercial-v1"
    minimum_dscr: Decimal = Decimal("1.20")
    maximum_debt_to_equity: Decimal = Decimal("2.00")
    minimum_current_ratio: Decimal = Decimal("1.10")
    maximum_ltv: Decimal = Decimal("0.80")


def evaluate_rules(
    metrics: list[MetricResult],
    *,
    missing_documents: list[str],
    thresholds: RiskThresholds | None = None,
) -> tuple[RiskLevel, list[RiskFlag]]:
    rules = thresholds or RiskThresholds()
    values = {metric.code: metric for metric in metrics}
    flags: list[RiskFlag] = []
    checks: list[tuple[str, Callable[[Decimal], bool], str, str]] = [
        (
            "DSCR",
            lambda x: x < rules.minimum_dscr,
            "LOW_DSCR",
            "Debt service coverage is below the illustrative institutional threshold.",
        ),
        (
            "DEBT_TO_EQUITY",
            lambda x: x > rules.maximum_debt_to_equity,
            "HIGH_LEVERAGE",
            "Leverage exceeds the illustrative institutional threshold.",
        ),
        (
            "CURRENT_RATIO",
            lambda x: x < rules.minimum_current_ratio,
            "LOW_LIQUIDITY",
            "Current ratio is below the illustrative institutional threshold.",
        ),
        (
            "LTV",
            lambda x: x > rules.maximum_ltv,
            "INSUFFICIENT_COLLATERAL",
            "Collateral coverage is below the illustrative institutional threshold.",
        ),
    ]
    for metric_code, fails, flag_code, reason in checks:
        metric = values.get(metric_code)
        if metric and metric.result is not None and fails(metric.result):
            flags.append(
                RiskFlag(
                    code=flag_code,
                    severity=RiskLevel.HIGH
                    if flag_code in {"LOW_DSCR", "HIGH_LEVERAGE"}
                    else RiskLevel.MODERATE,
                    reason=reason,
                    rule_version=rules.version,
                    source_ids=metric.source_ids,
                )
            )
    if missing_documents or any(metric.result is None for metric in metrics):
        flags.append(
            RiskFlag(
                code="MISSING_INFORMATION",
                severity=RiskLevel.INSUFFICIENT_DATA,
                reason="Required evidence or calculation inputs are missing.",
                rule_version=rules.version,
                source_ids=[],
            )
        )
        return RiskLevel.INSUFFICIENT_DATA, flags
    if any(flag.severity == RiskLevel.HIGH for flag in flags):
        return RiskLevel.HIGH, flags
    if flags:
        return RiskLevel.MODERATE, flags
    return RiskLevel.LOW, flags
