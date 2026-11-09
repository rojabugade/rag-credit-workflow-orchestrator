import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from creditflow.api.v1.dependencies import PrincipalDep
from creditflow.core.errors import NotFoundError

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get("/latest")
async def latest_evaluation(principal: PrincipalDep) -> dict[str, Any]:
    principal.require("analyst", "underwriter", "manager", "model_risk")
    path = Path("evals/reports/latest.json")
    if not path.exists():
        raise NotFoundError("evaluation report not available")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise NotFoundError("evaluation report is invalid")
    return value
