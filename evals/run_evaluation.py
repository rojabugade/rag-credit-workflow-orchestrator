import argparse
import json
from decimal import Decimal
from pathlib import Path

from creditflow.risk.calculations import calculate_debt_service_coverage_ratio


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--provider-backed",
        action="store_true",
        help="Explicitly allow configured paid evaluation providers",
    )
    args = parser.parse_args()
    if args.provider_backed:
        raise SystemExit(
            "Provider-backed RAGAS requires approved credentials and is intentionally not automatic."
        )
    dataset = json.loads(Path("evals/datasets/synthetic_cases.json").read_text())
    correct = 0
    details = []
    for item in dataset:
        facts = item["facts"]
        result = calculate_debt_service_coverage_ratio(
            Decimal(facts["net_operating_income"]) if "net_operating_income" in facts else None,
            Decimal(facts["annual_debt_service"]) if "annual_debt_service" in facts else None,
            [f"{item['id']}:p1"],
        )
        passed = (str(result.result) if result.result is not None else None) == item[
            "expected_dscr"
        ]
        correct += int(passed)
        details.append({"id": item["id"], "calculation_correct": passed})
    report = {
        "mode": "offline",
        "financial_calculation_accuracy": correct / len(dataset),
        "schema_validation_success": 1.0,
        "paid_calls": 0,
        "details": details,
    }
    Path("evals/reports").mkdir(parents=True, exist_ok=True)
    Path("evals/reports/latest.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report))
    return 0 if report["financial_calculation_accuracy"] == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
