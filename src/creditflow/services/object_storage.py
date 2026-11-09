import asyncio
from typing import Protocol

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from creditflow.core.errors import CreditFlowError


class ObjectStorage(Protocol):
    async def put(self, key: str, content: bytes, content_type: str, checksum: str) -> None: ...
    async def presigned_get(self, key: str, expires_seconds: int = 300) -> str: ...
    async def get(self, key: str) -> bytes: ...


class S3ObjectStorage:
    def __init__(
        self,
        *,
        bucket: str,
        region: str,
        endpoint_url: str | None = None,
        sse_algorithm: str = "AES256",
        kms_key_id: str | None = None,
    ) -> None:
        self.bucket = bucket
        self.sse_algorithm = sse_algorithm
        self.kms_key_id = kms_key_id
        self.client = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=endpoint_url,
            config=Config(
                connect_timeout=3, read_timeout=30, retries={"max_attempts": 3, "mode": "adaptive"}
            ),
        )

    async def put(self, key: str, content: bytes, content_type: str, checksum: str) -> None:
        try:
            arguments = {
                "Bucket": self.bucket,
                "Key": key,
                "Body": content,
                "ContentType": content_type,
                "Metadata": {"sha256": checksum},
                "ServerSideEncryption": self.sse_algorithm,
            }
            if self.kms_key_id:
                arguments["SSEKMSKeyId"] = self.kms_key_id
            await asyncio.to_thread(self.client.put_object, **arguments)
        except (BotoCoreError, ClientError) as exc:
            raise CreditFlowError("document storage failed") from exc

    async def presigned_get(self, key: str, expires_seconds: int = 300) -> str:
        if not 1 <= expires_seconds <= 900:
            raise ValueError("signed URL expiration must be between 1 and 900 seconds")
        try:
            return await asyncio.to_thread(
                self.client.generate_presigned_url,
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_seconds,
            )
        except (BotoCoreError, ClientError) as exc:
            raise CreditFlowError("signed URL generation failed") from exc

    async def get(self, key: str) -> bytes:
        try:
            response = await asyncio.to_thread(self.client.get_object, Bucket=self.bucket, Key=key)
            return await asyncio.to_thread(response["Body"].read)
        except (BotoCoreError, ClientError) as exc:
            raise CreditFlowError("document retrieval failed") from exc
