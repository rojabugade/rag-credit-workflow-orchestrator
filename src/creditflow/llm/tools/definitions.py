from creditflow.schemas.underwriting import MetricResult


def financial_tool_definitions() -> list[dict[str, object]]:
    definitions: list[dict[str, object]] = []
    for name in (
        "calculate_debt_service_coverage_ratio",
        "calculate_current_ratio",
        "calculate_debt_to_equity",
        "calculate_loan_to_value",
        "calculate_operating_margin",
    ):
        definitions.append(
            {
                "type": "function",
                "name": name,
                "description": "Run an allowlisted deterministic financial calculation; never estimate missing inputs.",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "numerator": {"type": ["number", "null"]},
                        "denominator": {"type": ["number", "null"]},
                        "source_ids": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["numerator", "denominator", "source_ids"],
                    "additionalProperties": False,
                },
            }
        )
    return definitions


def metric_json_schema() -> dict[str, object]:
    return MetricResult.model_json_schema()
