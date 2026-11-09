# Hybrid retrieval

Documents are normalized into page-preserving chunks with immutable citation IDs and SHA-256 hashes. Embeddings are versioned by provider/model/version/dimension. A dimension change creates a new table/index rather than mutating an existing vector column.

Retrieval applies tenant, visibility, jurisdiction, type, status, and effective-date filters to both vector and full-text branches. Reciprocal Rank Fusion (`k=60`) merges ranks; a configurable cross-encoder is the production reranker, with deterministic lexical reranking for offline mode. Only the highest-scoring bounded context is sent to an LLM. `validate_citations` rejects references absent from the retrieved set.

Cache keys include tenant, normalized query hash, filters, embedding/reranker versions, policy/document versions, prompt version, and model route. Policy or document updates increment versions and invalidate by namespace; sensitive cache values never cross tenant namespaces.
