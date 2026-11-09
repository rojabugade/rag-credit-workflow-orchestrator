import pytest
from httpx import ASGITransport, AsyncClient

from creditflow.main import app
from creditflow.services.runtime import runtime


@pytest.fixture(autouse=True)
def clear_runtime() -> None:
    runtime.cases.clear()
    runtime.documents.clear()
    runtime.jobs.clear()
    runtime.audits.clear()
    runtime.case_history.clear()
    runtime.idempotency.clear()


@pytest.mark.asyncio
async def test_complete_application_lifecycle_and_compatibility_alias() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post(
            "/api/v1/applications",
            headers={"Idempotency-Key": "application-lifecycle"},
            json={
                "borrower_name": "Synthetic Manufacturing LLC",
                "requested_amount": "125000.00",
                "currency": "USD",
                "jurisdiction": "US",
            },
        )
        assert created.status_code == 201, created.text
        application = created.json()
        assert application["assigned_analyst"] is None

        updated = await client.patch(
            f"/api/v1/applications/{application['id']}",
            json={
                "requested_amount": "130000.00",
                "expected_version": application["version"],
            },
        )
        assert updated.status_code == 200, updated.text
        application = updated.json()

        assigned = await client.put(
            f"/api/v1/applications/{application['id']}/assignment",
            headers={"X-Local-Roles": "manager"},
            json={
                "analyst_subject": "synthetic-analyst-2",
                "expected_version": application["version"],
            },
        )
        assert assigned.status_code == 200, assigned.text
        application = assigned.json()
        assert application["assigned_analyst"] == "synthetic-analyst-2"

        stale = await client.patch(
            f"/api/v1/applications/{application['id']}",
            json={"jurisdiction": "CA", "expected_version": 1},
        )
        assert stale.status_code == 409

        withdrawn = await client.post(
            f"/api/v1/applications/{application['id']}/withdraw",
            json={
                "rationale": "Synthetic borrower withdrew the application.",
                "expected_version": application["version"],
            },
        )
        assert withdrawn.status_code == 200, withdrawn.text
        assert withdrawn.json()["status"] == "WITHDRAWN"

        history = await client.get(f"/api/v1/applications/{application['id']}/history")
        assert [event["event_type"] for event in history.json()] == [
            "CASE_CREATED",
            "CASE_UPDATED",
            "CASE_ASSIGNED",
            "CASE_WITHDRAWN",
        ]

        compatibility = await client.get(f"/api/v1/cases/{application['id']}")
        assert compatibility.status_code == 200
