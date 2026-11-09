import asyncio
import json
from typing import Protocol

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from creditflow.core.errors import CreditFlowError
from creditflow.workers.sqs_worker import AnalysisMessage, IngestionMessage, QueueMessage


class JobQueue(Protocol):
    async def publish_analysis(self, message: AnalysisMessage) -> None: ...
    async def publish_ingestion(self, message: IngestionMessage) -> None: ...


class SQSJobQueue:
    def __init__(self, queue_url: str, *, region: str, endpoint_url: str | None = None) -> None:
        self.queue_url = queue_url
        self.client = boto3.client(
            "sqs",
            region_name=region,
            endpoint_url=endpoint_url,
            config=Config(connect_timeout=3, read_timeout=10, retries={"max_attempts": 3}),
        )

    async def publish_analysis(self, message: AnalysisMessage) -> None:
        await self._publish(message)

    async def publish_ingestion(self, message: IngestionMessage) -> None:
        await self._publish(message)

    async def _publish(self, message: QueueMessage) -> None:
        try:
            await asyncio.to_thread(
                self.client.send_message,
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message.model_dump(), separators=(",", ":")),
                MessageAttributes={
                    "schema_version": {
                        "DataType": "String",
                        "StringValue": message.schema_version,
                    }
                },
            )
        except (BotoCoreError, ClientError) as exc:
            raise CreditFlowError("analysis job dispatch failed") from exc
