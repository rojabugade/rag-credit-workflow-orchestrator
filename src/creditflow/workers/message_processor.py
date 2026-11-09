from creditflow.core.config import Settings
from creditflow.services.object_storage import S3ObjectStorage
from creditflow.workers.ingestion_processor import PostgresIngestionProcessor
from creditflow.workers.sqs_worker import AnalysisMessage, IngestionMessage, QueueMessage
from creditflow.workers.workflow_processor import PostgresWorkflowProcessor


class ProductionMessageProcessor:
    def __init__(self, settings: Settings) -> None:
        storage = S3ObjectStorage(
            bucket=settings.s3_bucket,
            region=settings.aws_region,
            endpoint_url=settings.s3_endpoint_url,
            sse_algorithm=settings.s3_sse_algorithm,
            kms_key_id=settings.s3_kms_key_id,
        )
        self.ingestion = PostgresIngestionProcessor(storage)
        self.analysis = PostgresWorkflowProcessor(settings)

    async def process(self, message: QueueMessage) -> None:
        if isinstance(message, IngestionMessage):
            await self.ingestion.process(message)
        elif isinstance(message, AnalysisMessage):
            await self.analysis.process(message)
        else:
            raise TypeError("unsupported queue message")
