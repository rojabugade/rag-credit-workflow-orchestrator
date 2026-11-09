from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from creditflow.retrieval.embeddings import EmbeddingProvider
from creditflow.retrieval.models import SearchFilters, SearchResult


class PostgresSearchBackend:
    """Tenant-filtered pgvector and PostgreSQL full-text retrieval backend."""

    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        embeddings: EmbeddingProvider,
        *,
        embedding_version: str = "1",
    ) -> None:
        self.sessions = sessions
        self.embeddings = embeddings
        self.embedding_version = embedding_version

    @asynccontextmanager
    async def _session(self, tenant_id: str) -> AsyncIterator[AsyncSession]:
        async with self.sessions() as session:
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": tenant_id},
            )
            yield session

    async def vector_search(
        self, query: str, filters: SearchFilters, limit: int
    ) -> list[SearchResult]:
        vectors = await self.embeddings.embed([query])
        vector_literal = "[" + ",".join(f"{value:.9f}" for value in vectors[0]) + "]"
        clauses, parameters = self._filters(filters)
        statement = text(
            f"""
            SELECT c.citation_id, c.content,
                   1 - (e.embedding <=> CAST(:query_vector AS vector)) AS score,
                   c.metadata_json, d.id AS document_id, d.document_type, v.version
            FROM document_chunk_embeddings e
            JOIN document_chunks c ON c.id = e.chunk_id
            JOIN document_versions v ON v.id = c.document_version_id
            JOIN documents d ON d.id = v.document_id
            JOIN embedding_models m ON m.id = e.embedding_model_id
            WHERE c.tenant_id = CAST(:tenant_id AS uuid)
              AND m.model = :embedding_model AND m.version = :embedding_version
              {clauses}
            ORDER BY e.embedding <=> CAST(:query_vector AS vector)
            LIMIT :limit
            """
        )
        if filters.allowed_document_ids:
            statement = statement.bindparams(bindparam("document_ids", expanding=True))
        parameters.update(
            query_vector=vector_literal,
            tenant_id=filters.tenant_id,
            embedding_model=self.embeddings.model,
            embedding_version=self.embedding_version,
            limit=limit,
        )
        async with self._session(filters.tenant_id) as session:
            rows = (await session.execute(statement, parameters)).mappings().all()
        return [self._result(row) for row in rows]

    async def keyword_search(
        self, query: str, filters: SearchFilters, limit: int
    ) -> list[SearchResult]:
        clauses, parameters = self._filters(filters)
        statement = text(
            f"""
            SELECT c.citation_id, c.content,
                   ts_rank_cd(c.search_vector, websearch_to_tsquery('english', :query)) AS score,
                   c.metadata_json, d.id AS document_id, d.document_type, v.version
            FROM document_chunks c
            JOIN document_versions v ON v.id = c.document_version_id
            JOIN documents d ON d.id = v.document_id
            WHERE c.tenant_id = CAST(:tenant_id AS uuid)
              AND c.search_vector @@ websearch_to_tsquery('english', :query)
              {clauses}
            ORDER BY score DESC, c.citation_id
            LIMIT :limit
            """
        )
        if filters.allowed_document_ids:
            statement = statement.bindparams(bindparam("document_ids", expanding=True))
        parameters.update(query=query, tenant_id=filters.tenant_id, limit=limit)
        async with self._session(filters.tenant_id) as session:
            rows = (await session.execute(statement, parameters)).mappings().all()
        return [self._result(row) for row in rows]

    def _filters(self, filters: SearchFilters) -> tuple[str, dict[str, Any]]:
        clauses: list[str] = []
        parameters: dict[str, Any] = {}
        if filters.document_type:
            clauses.append("AND d.document_type = :document_type")
            parameters["document_type"] = filters.document_type
        if filters.allowed_document_ids:
            clauses.append("AND d.id IN :document_ids")
            parameters["document_ids"] = list(filters.allowed_document_ids)
        if filters.jurisdiction:
            clauses.append(
                "AND COALESCE(c.metadata_json->>'jurisdiction', :jurisdiction) = :jurisdiction"
            )
            parameters["jurisdiction"] = filters.jurisdiction
        return "\n".join(clauses), parameters

    def _result(self, row: Any) -> SearchResult:
        metadata = dict(row["metadata_json"] or {})
        metadata.update(
            document_id=str(row["document_id"]),
            document_type=str(row["document_type"]),
            version=str(row["version"]),
        )
        return SearchResult(
            citation_id=str(row["citation_id"]),
            text=str(row["content"]),
            score=float(row["score"]),
            metadata={key: str(value) for key, value in metadata.items()},
        )
