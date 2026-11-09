from uuid import UUID

import pytest

from creditflow.auth.dependencies import LOCAL_TENANT_ID
from creditflow.core.config import get_settings
from creditflow.mcp.client import CreditRiskMCPClient
from creditflow.mcp.server import mcp
from creditflow.schemas.underwriting import CaseCreate
from creditflow.services.runtime import runtime


@pytest.fixture(autouse=True)
def clear_runtime() -> None:
    runtime.cases.clear()
    runtime.audits.clear()
    runtime.case_history.clear()
    runtime.tool_logs.clear()
    runtime.idempotency.clear()


@pytest.mark.asyncio
async def test_authenticated_mcp_client_reads_tenant_scoped_application() -> None:
    application, _ = await runtime.create_case(
        LOCAL_TENANT_ID,
        "local-analyst",
        CaseCreate(
            borrower_name="Synthetic MCP LLC",
            requested_amount="250000.00",
            currency="USD",
            jurisdiction="US",
        ),
        "mcp-case-key",
    )
    client = CreditRiskMCPClient(
        mcp,
        token=get_settings().mcp_auth_token,
        tenant_id=LOCAL_TENANT_ID,
        subject="local-analyst",
        roles=["analyst"],
    )
    result = await client.call("get_loan_application", {"application_id": str(application["id"])})
    assert result["borrower_name"] == "Synthetic MCP LLC"
    assert runtime.tool_logs[-1]["subject"] == "local-analyst"


@pytest.mark.asyncio
async def test_mcp_tenant_boundary_hides_application() -> None:
    application, _ = await runtime.create_case(
        LOCAL_TENANT_ID,
        "local-analyst",
        CaseCreate(borrower_name="Hidden LLC", requested_amount="1000.00"),
        "mcp-hidden-key",
    )
    client = CreditRiskMCPClient(
        mcp,
        token=get_settings().mcp_auth_token,
        tenant_id=UUID("00000000-0000-0000-0000-000000000099"),
        subject="other-analyst",
        roles=["analyst"],
    )
    with pytest.raises(RuntimeError, match="Error executing tool"):
        await client.call("get_loan_application", {"application_id": str(application["id"])})
