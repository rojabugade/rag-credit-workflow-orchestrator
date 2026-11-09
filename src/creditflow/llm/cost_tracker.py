import asyncio
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ModelPricing:
    input_usd_per_million: Decimal
    output_usd_per_million: Decimal


@dataclass(frozen=True)
class UsageRecord:
    tenant_id: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: Decimal


def estimate_cost(input_tokens: int, output_tokens: int, pricing: ModelPricing) -> Decimal:
    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("token counts cannot be negative")
    million = Decimal(1_000_000)
    return (
        Decimal(input_tokens) * pricing.input_usd_per_million / million
        + Decimal(output_tokens) * pricing.output_usd_per_million / million
    ).quantize(Decimal("0.000001"))


class InMemoryUsageLedger:
    """Test/local ledger; production writes equivalent records transactionally to PostgreSQL."""

    def __init__(self) -> None:
        self._records: list[UsageRecord] = []
        self._lock = asyncio.Lock()

    async def record(self, usage: UsageRecord) -> None:
        async with self._lock:
            self._records.append(usage)

    async def tenant_total(self, tenant_id: str) -> Decimal:
        async with self._lock:
            return sum(
                (item.estimated_cost_usd for item in self._records if item.tenant_id == tenant_id),
                start=Decimal("0"),
            )
