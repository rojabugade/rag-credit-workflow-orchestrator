import hmac
from typing import Any, cast
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from mcp.server import MCPServer
from pydantic import BaseModel, ConfigDict, Field

from creditflow.compliance.policy_catalog import search_effective_policies
from creditflow.core.config import get_settings
from creditflow.core.errors import AuthorizationError, NotFoundError
from creditflow.services.runtime import runtime
from creditflow.workflows.agents.financial import financial_analysis
from creditflow.workflows.state import UnderwritingState


class ToolAuthorization(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=16)
    tenant_id: UUID
    subject: str = Field(min_length=1, max_length=255)
    roles: list[str] = Field(min_length=1)


def _authorize(auth: ToolAuthorization, *roles: str) -> None:
    configured = get_settings().mcp_auth_token
    if not hmac.compare_digest(auth.token, configured):
        raise AuthorizationError("invalid MCP authentication token")
    if not set(auth.roles).intersection(roles):
        raise AuthorizationError("MCP caller lacks the required role")


def _case(auth: ToolAuthorization, application_id: str) -> dict[str, Any]:
    _authorize(auth, "analyst", "underwriter", "manager")
    item = runtime._case(auth.tenant_id, UUID(application_id))
    runtime.tool_logs.append(
        {
            "tool": "case_access",
            "tenant_id": str(auth.tenant_id),
            "subject": auth.subject,
            "application_id": application_id,
        }
    )
    return item


mcp = MCPServer(
    "CreditRisk AI",
    version="1.0.0",
    instructions="Read-only, tenant-isolated underwriting tools. Human review is always required.",
)


@mcp.tool()
async def get_loan_application(auth: ToolAuthorization, application_id: str) -> dict[str, Any]:
    """Return one authorized synthetic application without internal workflow state."""
    item = _case(auth, application_id)
    allowed = {
        "id",
        "borrower_name",
        "requested_amount",
        "currency",
        "jurisdiction",
        "status",
        "version",
        "assigned_analyst",
        "created_at",
        "updated_at",
    }
    encoded = jsonable_encoder({key: value for key, value in item.items() if key in allowed})
    return cast("dict[str, Any]", encoded)


@mcp.tool()
async def get_financial_statement(auth: ToolAuthorization, application_id: str) -> dict[str, Any]:
    """Return validated extracted facts and source identifiers for an authorized application."""
    item = _case(auth, application_id)
    return {"facts": item.get("facts", {}), "source_ids": item.get("source_ids", [])}


@mcp.tool()
async def calculate_financial_ratios(
    auth: ToolAuthorization, application_id: str
) -> dict[str, Any]:
    """Run deterministic Decimal-based ratios; never asks an LLM to calculate."""
    item = _case(auth, application_id)
    state = cast(
        "UnderwritingState",
        {
            "case_id": application_id,
            "tenant_id": str(auth.tenant_id),
            "borrower_name": str(item["borrower_name"]),
            "requested_amount": str(item["requested_amount"]),
            "facts": item.get("facts", {}),
            "source_ids": item.get("source_ids", []),
            "evidence": item.get("evidence", []),
            "missing_documents": item.get("missing_documents", []),
            "policy_versions": item.get("policy_versions", []),
        },
    )
    result = financial_analysis(state)
    return cast("dict[str, Any]", jsonable_encoder(result))


@mcp.tool()
async def retrieve_lending_policy(
    auth: ToolAuthorization, query: str, effective_on: str
) -> list[dict[str, Any]]:
    """Retrieve effective fictional policy passages for an authorized analyst."""
    from datetime import date

    _authorize(auth, "analyst", "underwriter", "manager", "policy_admin")
    policies = search_effective_policies(query, date.fromisoformat(effective_on))
    return cast("list[dict[str, Any]]", jsonable_encoder(policies))


@mcp.tool()
async def get_credit_analysis(auth: ToolAuthorization, application_id: str) -> dict[str, Any]:
    """Return the current evidence-backed recommendation, never a final credit decision."""
    item = _case(auth, application_id)
    analysis = item.get("analysis")
    if not isinstance(analysis, dict):
        raise NotFoundError("analysis not available")
    return cast("dict[str, Any]", jsonable_encoder(analysis))


@mcp.tool()
async def generate_underwriting_summary(
    auth: ToolAuthorization, application_id: str
) -> dict[str, Any]:
    """Return the already-validated report; this tool cannot approve or reject credit."""
    item = _case(auth, application_id)
    if not item.get("analysis"):
        raise NotFoundError("analysis not available")
    return {
        "application_id": application_id,
        "recommendation": jsonable_encoder(item["analysis"]),
        "report_markdown": str(item.get("report_markdown", "")),
        "human_review_required": True,
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
