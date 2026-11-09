import asyncio
import contextlib
import json
import signal
from typing import Annotated, Any, Literal, Protocol

import boto3
import structlog
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

log = structlog.get_logger()


class AnalysisMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message_type: Literal["analysis"] = "analysis"
    schema_version: str
    job_id: str
    case_id: str
    tenant_id: str
    idempotency_key: str


class IngestionMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message_type: Literal["ingestion"] = "ingestion"
    schema_version: str
    document_id: str
    document_version_id: str
    case_id: str
    tenant_id: str
    actor: str


QueueMessage = Annotated[AnalysisMessage | IngestionMessage, Field(discriminator="message_type")]
message_adapter: TypeAdapter[QueueMessage] = TypeAdapter(QueueMessage)


class AnalysisProcessor(Protocol):
    async def process(self, message: QueueMessage) -> None: ...


class SQSWorker:
    def __init__(
        self,
        queue_url: str,
        *,
        processor: AnalysisProcessor,
        concurrency: int = 4,
        visibility_timeout: int = 300,
        region: str = "us-east-1",
        endpoint_url: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.queue_url = queue_url
        self.processor = processor
        self.visibility_timeout = visibility_timeout
        self.client = client or boto3.client(
            "sqs",
            region_name=region,
            endpoint_url=endpoint_url,
            config=Config(
                connect_timeout=3, read_timeout=25, retries={"max_attempts": 5, "mode": "adaptive"}
            ),
        )
        self.semaphore = asyncio.Semaphore(concurrency)
        self.stopping = asyncio.Event()

    async def run(self) -> None:
        while not self.stopping.is_set():
            try:
                response = await asyncio.to_thread(
                    self.client.receive_message,
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=20,
                    VisibilityTimeout=self.visibility_timeout,
                    AttributeNames=["ApproximateReceiveCount"],
                )
            except (BotoCoreError, ClientError):
                log.exception("sqs_receive_failed")
                await asyncio.sleep(2)
                continue
            for raw in response.get("Messages", []):
                asyncio.create_task(self._guarded_process(raw))

    async def _guarded_process(self, raw: dict[str, Any]) -> None:
        async with self.semaphore:
            heartbeat = asyncio.create_task(self._heartbeat(raw["ReceiptHandle"]))
            try:
                message = message_adapter.validate_python(json.loads(raw["Body"]))
                await self.processor.process(message)
                await asyncio.to_thread(
                    self.client.delete_message,
                    QueueUrl=self.queue_url,
                    ReceiptHandle=raw["ReceiptHandle"],
                )
            except Exception:
                log.exception("sqs_message_failed", message_id=raw.get("MessageId"))
                # No delete: SQS retries and eventually applies the configured DLQ redrive policy.
            finally:
                heartbeat.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await heartbeat

    async def _heartbeat(self, receipt_handle: str) -> None:
        while True:
            await asyncio.sleep(self.visibility_timeout / 2)
            await asyncio.to_thread(
                self.client.change_message_visibility,
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle,
                VisibilityTimeout=self.visibility_timeout,
            )


async def main() -> None:
    from creditflow.core.config import get_settings
    from creditflow.workers.message_processor import ProductionMessageProcessor

    settings = get_settings()
    if not settings.sqs_queue_url:
        raise ValueError("CREDITFLOW_SQS_QUEUE_URL is required")
    worker = SQSWorker(
        settings.sqs_queue_url,
        processor=ProductionMessageProcessor(settings),
        concurrency=settings.worker_concurrency,
        region=settings.aws_region,
        endpoint_url=settings.sqs_endpoint_url,
    )
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, worker.stopping.set)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
