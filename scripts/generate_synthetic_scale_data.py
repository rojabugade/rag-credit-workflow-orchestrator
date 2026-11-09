import argparse
import json
import random
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Stream reproducible fictional scale fixtures")
    parser.add_argument("--financial-records", type=int, default=1_000)
    parser.add_argument("--policy-chunks", type=int, default=1_000)
    parser.add_argument("--output", type=Path, default=Path("data/synthetic"))
    args = parser.parse_args()
    if args.financial_records < 1 or args.policy_chunks < 1:
        raise SystemExit("record counts must be positive")
    args.output.mkdir(parents=True, exist_ok=True)
    randomizer = random.Random(42)  # noqa: S311 - reproducible synthetic fixtures, not security
    with (args.output / "financial_records.jsonl").open("w", encoding="utf-8") as target:
        for index in range(args.financial_records):
            revenue = randomizer.randint(100_000, 50_000_000)
            target.write(
                json.dumps(
                    {
                        "borrower_id": f"SYN-{index:09d}",
                        "period": "2025-12-31",
                        "revenue": revenue,
                        "operating_income": int(revenue * randomizer.uniform(0.03, 0.3)),
                        "synthetic": True,
                    }
                )
                + "\n"
            )
    with (args.output / "policy_chunks.jsonl").open("w", encoding="utf-8") as target:
        for index in range(args.policy_chunks):
            target.write(
                json.dumps(
                    {
                        "citation_id": f"fictional-policy-v1:section-{index}",
                        "text": f"Fictional lending policy passage {index}; human review required.",
                        "version": "fictional-v1",
                        "synthetic": True,
                    }
                )
                + "\n"
            )
    print(
        json.dumps(
            {
                "financial_records": args.financial_records,
                "policy_chunks": args.policy_chunks,
                "seed": 42,
            }
        )
    )


if __name__ == "__main__":
    main()
