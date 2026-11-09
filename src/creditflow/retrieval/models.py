from dataclasses import dataclass, field
from datetime import date
from typing import Protocol


@dataclass(frozen=True)
class SearchFilters:
    tenant_id: str
    document_type: str | None = None
    jurisdiction: str | None = None
    effective_on: date | None = None
    allowed_document_ids: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class SearchResult:
    citation_id: str
    text: str
    score: float
    metadata: dict[str, str]


class SearchBackend(Protocol):
    async def vector_search(
        self, query: str, filters: SearchFilters, limit: int
    ) -> list[SearchResult]: ...

    async def keyword_search(
        self, query: str, filters: SearchFilters, limit: int
    ) -> list[SearchResult]: ...
