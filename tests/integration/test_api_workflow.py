import asyncio

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
async def test_health_compatibility_alias_is_ready_in_mock_mode() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "mode": "mock"}


@pytest.mark.asyncio
async def test_low_risk_case_interrupts_and_resumes() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post(
            "/api/v1/cases",
            headers={"Idempotency-Key": "create-case-a"},
            json={
                "borrower_name": "Synthetic Stable LLC",
                "requested_amount": "500000.00",
                "currency": "USD",
                "jurisdiction": "US",
            },
        )
        assert created.status_code == 201, created.text
        case = created.json()
        csv_data = b"metric,value\nnet_operating_income,270000\nannual_debt_service,180000\ncurrent_assets,800000\ncurrent_liabilities,400000\ntotal_debt,600000\ntotal_equity,800000\ncollateral_value,900000\noperating_income,200000\nrevenue,1000000\n"
        uploaded = await client.post(
            f"/api/v1/cases/{case['id']}/documents",
            files={"file": ("financials.csv", csv_data, "text/csv")},
        )
        assert uploaded.status_code == 201, uploaded.text
        started = await client.post(
            f"/api/v1/cases/{case['id']}/analyze", headers={"Idempotency-Key": "analysis-case-a"}
        )
        assert started.status_code == 202
        job_id = started.json()["id"]
        for _ in range(50):
            job = (await client.get(f"/api/v1/jobs/{job_id}")).json()
            if job["status"] != "RUNNING" and job["status"] != "QUEUED":
                break
            await asyncio.sleep(0.02)
        assert job["status"] == "AWAITING_HUMAN_REVIEW", job
        analysis = (await client.get(f"/api/v1/cases/{case['id']}/analysis")).json()
        assert analysis["risk_level"] == "LOW"
        refreshed = (await client.get(f"/api/v1/cases/{case['id']}")).json()
        review = await client.post(
            f"/api/v1/cases/{case['id']}/review",
            json={
                "action": "ACCEPT",
                "rationale": "Evidence and calculations reviewed by authorized analyst.",
                "expected_case_version": refreshed["version"],
            },
        )
        assert review.status_code == 201, review.text
        audit = (await client.get(f"/api/v1/cases/{case['id']}/audit")).json()
        assert audit["total"] == 5


@pytest.mark.asyncio
async def test_cross_tenant_case_is_hidden() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post(
            "/api/v1/cases",
            headers={"Idempotency-Key": "tenant-case"},
            json={
                "borrower_name": "Synthetic LLC",
                "requested_amount": "1000",
                "currency": "USD",
                "jurisdiction": "US",
            },
        )
        case_id = created.json()["id"]
        runtime.cases[next(iter(runtime.cases))]["tenant_id"] = __import__("uuid").uuid4()
        response = await client.get(f"/api/v1/cases/{case_id}")
        assert response.status_code == 404
