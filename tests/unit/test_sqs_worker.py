import json
from typing import Any

import pytest

from creditflow.workers.sqs_worker import AnalysisMessage, SQSWorker


class RecordingProcessor:
    def __init__(self) -> None:
        self.messages: list[AnalysisMessage] = []

    async def process(self, message: AnalysisMessage) -> None:
        self.messages.append(message)


class FakeSQSClient:
    def __init__(self) -> None:
        self.deleted: list[dict[str, Any]] = []

    def delete_message(self, **kwargs: Any) -> None:
        self.deleted.append(kwargs)

    def change_message_visibility(self, **kwargs: Any) -> None:
        del kwargs


@pytest.mark.asyncio
async def test_worker_invokes_injected_processor_before_acknowledging() -> None:
    processor = RecordingProcessor()
    fake = FakeSQSClient()
    worker = SQSWorker("https://example.invalid/queue", processor=processor, client=fake)
    body = {
        "message_type": "analysis",
        "schema_version": "1",
        "job_id": "00000000-0000-0000-0000-000000000010",
        "case_id": "00000000-0000-0000-0000-000000000011",
        "tenant_id": "00000000-0000-0000-0000-000000000001",
        "idempotency_key": "synthetic-job-key",
    }
    await worker._guarded_process(
        {"Body": json.dumps(body), "ReceiptHandle": "receipt", "MessageId": "message"}
    )
    assert processor.messages[0].job_id == body["job_id"]
    assert fake.deleted[0]["ReceiptHandle"] == "receipt"
