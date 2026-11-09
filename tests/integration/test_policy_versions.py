import pytest
from httpx import ASGITransport, AsyncClient

from creditflow.main import app


@pytest.mark.asyncio
async def test_policy_search_respects_effective_date() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        old = await client.post(
            "/api/v1/policies/search",
            json={"effective_on": "2026-06-01"},
        )
        new = await client.post(
            "/api/v1/policies/search",
            json={"effective_on": "2027-06-01"},
        )
        assert old.json()["items"][0]["policy_version"] == "synthetic-commercial-v1"
        assert new.json()["items"][0]["policy_version"] == "synthetic-commercial-v2"
