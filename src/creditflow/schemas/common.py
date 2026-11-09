from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ErrorDetail(StrictModel):
    code: str
    message: str
    request_id: str
    details: dict[str, object] = Field(default_factory=dict)


class ErrorResponse(StrictModel):
    error: ErrorDetail


class Page[T](StrictModel):
    items: list[T]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)


class EvidenceRef(StrictModel):
    source_id: str = Field(
        pattern=r"^[A-Za-z0-9_-]+:(p\d+(?::c\d+)?|row\d+|section-[A-Za-z0-9_.-]+)$"
    )
    document_id: UUID
    version: int = Field(ge=1)
    excerpt_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    page: int | None = Field(default=None, ge=1)
    heading: str | None = None
