# Interview guide

## Problem and flow
CreditFlow reduces evidence assembly and consistency work in commercial underwriting while keeping decisions with authorized people. A user creates a case, uploads versioned evidence, queues analysis, and a worker resumes a LangGraph thread. Extraction preserves source locations; deterministic tools compute ratios; hybrid RAG retrieves effective policies; risk/compliance findings join at verification; a report pauses at a human interrupt; review and evidence hashes are audited.

## Why these choices
- **FastAPI:** async I/O, Pydantic/OpenAPI contracts, dependency injection, and a small operational footprint.
- **LangGraph:** explicit state, conditional recovery, durable checkpoints, fan-out/join, and first-class human interrupts. State is local memory only in tests and PostgreSQL through `PostgresSaver` in production composition.
- **PostgreSQL/pgvector:** transactionally co-locates metadata, FTS, vectors, policy versions, checkpoints, and audit references. HNSW improves approximate vector lookup; GIN supports FTS.
- **Hybrid + reranking:** semantic search handles paraphrases, FTS preserves exact policy/financial terminology, RRF avoids incomparable score calibration, and a cross-encoder spends more compute only on a candidate shortlist.

## Correctness and AI boundaries
Function calling controls which allowlisted calculation/retrieval operation a model may request; structured output constrains the final shape. Pydantic validates both. Decimal Python functions own formulas and provenance—the model explains results but never invents arithmetic. Citation validation compares every source ID with retrieved immutable IDs; missing/stale/conflicting evidence causes bounded correction then escalation.

The direct OpenAI adapter uses the Responses API (`responses.parse`), handles refusal/incomplete output, and does not use Assistants. Provider routing normalizes capabilities; fallback is allowed only when a provider supports the required schema/tools. Redis keys include tenant and all source/policy/prompt/model versions. This reduces duplicate work without serving stale or cross-tenant recommendations.

## Reliability and concurrency
HTTP only enqueues long work. SQS provides at-least-once delivery; jobs claim a unique tenant/idempotency key, heartbeat visibility, delete only after commit, back off, and eventually enter a DLQ. Optimistic case versions reject stale reviews. Checkpoints reuse the same thread ID; side effects are transactionally idempotent and occur outside replay-prone interrupt code.

API and worker ECS services communicate through SQS/data stores in private subnets. API target tracking and worker queue-depth tracking scale independently. Immutable image SHAs and expand/contract migrations permit rollback.

## Observability and failures
Logs explain discrete events, metrics quantify aggregate behavior, and traces connect latency across components. Sensitive text is excluded/sanitized. Likely failures include malformed/OCR documents, provider timeouts/refusals, embedding-version mismatch, policy staleness, DB pool exhaustion, poison messages, and reviewer races. Each has explicit failure/escalation behavior.

## What can be claimed
The code demonstrates architecture and measured local tests. It does **not** prove 120k records, 15M policies, 1M monthly calls, 35% analyst savings, 31% retrieval gains, 42% defect reduction, 27% cost savings, or sub-450ms full analysis. `docs/performance.md` defines experiments needed to make those claims responsibly.

## Six resume-theme mappings
1. **Multi-agent underwriting:** `workflows/graph.py`, typed state, agents, verification, human interrupt.
2. **Accurate hybrid RAG:** `retrieval/hybrid.py`, pgvector/FTS/HNSW migration, citation tests.
3. **Integration quality:** Pydantic schemas, Responses adapter, ingestion validators, standardized API errors.
4. **Inference cost optimization:** provider abstraction, bounded context/retries, versioned cache design, usage metrics.
5. **Cloud scale/reliability:** SQS worker contract, ECS split, queue autoscaling, DLQ/visibility and idempotency design.
6. **Audit/security/observability:** OIDC/RBAC/RLS, KMS/Object Lock design, hash chains, Prometheus/Grafana/OTel hooks.
