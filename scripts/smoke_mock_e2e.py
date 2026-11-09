"""Run the complete credential-free mock underwriting path against a live API."""

import asyncio
import json
from typing import Any
from uuid import uuid4

import httpx


async def main() -> None:
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=20) as client:
        ready = await client.get("/health/ready")
        ready.raise_for_status()
        compatibility_health = await client.get("/health")
        compatibility_health.raise_for_status()

        created = await client.post(
            "/api/v1/applications",
            headers={"Idempotency-Key": f"smoke-create-{uuid4()}"},
            json={
                "borrower_name": "Synthetic Smoke Test LLC",
                "requested_amount": "500000.00",
                "currency": "USD",
                "jurisdiction": "US",
            },
        )
        created.raise_for_status()
        application = created.json()
        application_id = application["id"]

        csv_data = (
            b"metric,value\n"
            b"net_operating_income,270000\n"
            b"annual_debt_service,180000\n"
            b"current_assets,800000\n"
            b"current_liabilities,400000\n"
            b"total_debt,600000\n"
            b"total_equity,800000\n"
            b"collateral_value,900000\n"
            b"operating_income,200000\n"
            b"revenue,1000000\n"
        )
        uploaded = await client.post(
            f"/api/v1/cases/{application_id}/documents",
            files={"file": ("synthetic-financials.csv", csv_data, "text/csv")},
        )
        uploaded.raise_for_status()

        started = await client.post(
            f"/api/v1/cases/{application_id}/analyze",
            headers={"Idempotency-Key": f"smoke-analysis-{uuid4()}"},
        )
        started.raise_for_status()
        job_id = started.json()["id"]
        job: dict[str, Any] = {}
        for _ in range(100):
            job_response = await client.get(f"/api/v1/jobs/{job_id}")
            job_response.raise_for_status()
            job = job_response.json()
            if job["status"] not in {"QUEUED", "RUNNING"}:
                break
            await asyncio.sleep(0.02)
        if job.get("status") != "AWAITING_HUMAN_REVIEW":
            raise RuntimeError(f"analysis did not reach human review: {job}")

        analysis_response = await client.get(f"/api/v1/cases/{application_id}/analysis")
        analysis_response.raise_for_status()
        analysis = analysis_response.json()

        assistant_response = await client.post(
            f"/api/v1/applications/{application_id}/assistant/stream",
            json={"question": "What recommendation and risk level were validated?"},
        )
        assistant_response.raise_for_status()
        assistant_events = [
            json.loads(line.removeprefix("data: "))
            for line in assistant_response.text.splitlines()
            if line.startswith("data: ")
        ]
        if not any(event.get("type") == "done" for event in assistant_events):
            raise RuntimeError("assistant stream did not finish")

        evaluation = await client.get("/api/v1/evaluations/latest")
        evaluation.raise_for_status()

        refreshed_response = await client.get(f"/api/v1/applications/{application_id}")
        refreshed_response.raise_for_status()
        refreshed = refreshed_response.json()
        review = await client.post(
            f"/api/v1/cases/{application_id}/review",
            json={
                "action": "ACCEPT",
                "rationale": "Synthetic evidence and deterministic calculations reviewed.",
                "expected_case_version": refreshed["version"],
            },
        )
        review.raise_for_status()

        audit_response = await client.get(f"/api/v1/cases/{application_id}/audit")
        audit_response.raise_for_status()
        audit = audit_response.json()
        print(
            json.dumps(
                {
                    "health": compatibility_health.json(),
                    "application_id": application_id,
                    "job_status_before_review": job["status"],
                    "risk_level": analysis["risk_level"],
                    "recommendation": analysis["recommendation"],
                    "assistant_stream_completed": True,
                    "evaluation_mode": evaluation.json()["mode"],
                    "human_review": review.json()["action"],
                    "audit_events": audit["total"],
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
