from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CREDITFLOW_", env_file=".env", extra="ignore")

    env: Literal["local", "test", "staging", "production"] = "local"
    runtime_backend: Literal["local", "postgres"] = "local"
    mock_llm_mode: bool = True
    local_auth_enabled: bool = True
    database_url: str = "sqlite+aiosqlite:///./creditflow.db"
    checkpoint_database_url: str | None = None
    redis_url: str = "redis://localhost:6379/0"
    s3_endpoint_url: str | None = None
    s3_bucket: str = "creditflow-documents"
    s3_sse_algorithm: Literal["AES256", "aws:kms"] = "AES256"
    s3_kms_key_id: str | None = None
    aws_region: str = "us-east-1"
    sqs_queue_url: str | None = None
    sqs_endpoint_url: str | None = None
    worker_concurrency: int = Field(default=4, ge=1, le=64)
    oidc_issuer: str | None = None
    oidc_jwks_url: str | None = None
    oidc_audience: str = "creditflow-api"
    openai_api_key: str | None = Field(default=None, repr=False)
    openai_model: str = "gpt-5-mini"
    anthropic_api_key: str | None = Field(default=None, repr=False)
    anthropic_model: str = "claude-sonnet-4-5"
    bedrock_model: str | None = None
    litellm_enabled: bool = False
    llm_simple_alias: str = "credit-simple"
    llm_complex_alias: str = "credit-complex"
    sensitive_llm_cache_enabled: bool = False
    mcp_auth_token: str = Field(default="local-mcp-token-change-me", repr=False)
    max_upload_bytes: int = 20 * 1024 * 1024
    workflow_max_retries: int = 2
    request_timeout_seconds: float = 30.0
    langsmith_tracing: bool = False
    otel_exporter_otlp_endpoint: str | None = None
    log_level: str = "INFO"

    @model_validator(mode="after")
    def secure_production(self) -> "Settings":
        if self.env in {"staging", "production"} and self.local_auth_enabled:
            raise ValueError("local authentication is forbidden outside local/test")
        if self.env == "production" and (
            not self.oidc_issuer or not self.oidc_jwks_url or self.mock_llm_mode
        ):
            raise ValueError("production requires OIDC and a live LLM provider")
        if self.env in {"staging", "production"} and (not self.sqs_queue_url or not self.s3_bucket):
            raise ValueError("deployed environments require SQS and S3 configuration")
        if self.env == "production" and (
            self.s3_sse_algorithm != "aws:kms" or not self.s3_kms_key_id
        ):
            raise ValueError("production document storage requires an explicit KMS key")
        if (
            self.env == "production" and self.mcp_auth_token == "local-mcp-token-change-me"  # noqa: S105
        ):
            raise ValueError("production requires a rotated MCP authentication token")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
