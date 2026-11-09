import asyncio
from pathlib import Path

import httpx

CASES = [
    ("Synthetic Stable LLC", "500000.00", "case_a_financials.csv"),
    ("Synthetic Leveraged LLC", "500000.00", "case_b_financials.csv"),
    ("Synthetic Incomplete LLC", "250000.00", "case_c_incomplete.csv"),
]


async def main() -> None:
    async with httpx.AsyncClient(base_url="http://api:8000", timeout=30) as client:
        for index, (borrower, amount, filename) in enumerate(CASES, start=1):
            response = await client.post(
                "/api/v1/cases",
                headers={"Idempotency-Key": f"synthetic-seed-case-{index}"},
                json={
                    "borrower_name": borrower,
                    "requested_amount": amount,
                    "currency": "USD",
                    "jurisdiction": "US",
                },
            )
            response.raise_for_status()
            case_id = response.json()["id"]
            path = Path("sample_data/documents") / filename
            with path.open("rb") as source:
                upload = await client.post(
                    f"/api/v1/cases/{case_id}/documents",
                    files={"file": (filename, source, "text/csv")},
                )
            upload.raise_for_status()
            analysis = await client.post(
                f"/api/v1/cases/{case_id}/analyze",
                headers={"Idempotency-Key": f"synthetic-seed-analysis-{index}"},
            )
            analysis.raise_for_status()
            print(f"{borrower}: case={case_id} job={analysis.json()['id']}")


if __name__ == "__main__":
    asyncio.run(main())
