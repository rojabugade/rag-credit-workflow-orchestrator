import pytest

from creditflow.core.errors import ProviderError
from creditflow.llm.providers.mock import DeterministicMockProvider
from creditflow.schemas.underwriting import ReviewRequest


@pytest.mark.asyncio
async def test_malformed_mock_provider_output_fails_closed() -> None:
    provider = DeterministicMockProvider()
    with pytest.raises(ProviderError):
        await provider.structured(
            instructions="Return review",
            input_text='{"action":"ACCEPT"}',
            output_type=ReviewRequest,
        )
