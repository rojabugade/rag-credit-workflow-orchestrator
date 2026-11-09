from pydantic import BaseModel, ConfigDict

from creditflow.evaluation.schema_eval import schema_validation_rate


class StrictFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    risk_level: str
    review_required: bool


def test_unvalidated_payloads_are_measured_against_strict_schema() -> None:
    report = schema_validation_rate(
        [
            {"risk_level": "LOW", "review_required": True},
            {"risk_level": "HIGH"},
            {"risk_level": "LOW", "review_required": True, "invented": "field"},
        ],
        StrictFinding,
    )
    assert report["sample_size"] == 3
    assert report["valid"] == 1
    assert report["validation_rate"] == 1 / 3
