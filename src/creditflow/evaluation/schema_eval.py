from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel, ValidationError


def schema_validation_rate(
    payloads: Iterable[dict[str, Any]], schema: type[BaseModel]
) -> dict[str, Any]:
    total = 0
    failures: list[dict[str, Any]] = []
    for index, payload in enumerate(payloads):
        total += 1
        try:
            schema.model_validate(payload)
        except ValidationError as exc:
            failures.append({"index": index, "errors": exc.errors(include_url=False)})
    return {
        "sample_size": total,
        "valid": total - len(failures),
        "validation_rate": (total - len(failures)) / total if total else 0.0,
        "failures": failures,
    }
