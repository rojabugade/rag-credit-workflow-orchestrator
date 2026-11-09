from typing import Any
from uuid import UUID

from mcp import Client
from mcp.server import MCPServer


class CreditRiskMCPClient:
    def __init__(
        self,
        server: str | MCPServer[Any],
        *,
        token: str,
        tenant_id: UUID,
        subject: str,
        roles: list[str],
    ) -> None:
        self._server = server
        self._authorization = {
            "token": token,
            "tenant_id": str(tenant_id),
            "subject": subject,
            "roles": roles,
        }

    async def call(self, tool: str, arguments: dict[str, object]) -> dict[str, Any] | list[Any]:
        payload = {"auth": self._authorization, **arguments}
        async with Client(self._server, raise_exceptions=True) as client:
            result = await client.call_tool(tool, payload)
        if result.is_error:
            messages = [str(getattr(item, "text", "MCP tool failed")) for item in result.content]
            raise RuntimeError("; ".join(messages))
        structured = result.structured_content
        if isinstance(structured, (dict, list)):
            return structured
        raise RuntimeError("MCP tool did not return structured content")
