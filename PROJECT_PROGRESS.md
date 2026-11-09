# CreditRisk AI project progress

Updated: 2026-11-05

This is the authoritative phase tracker. Verified capabilities are distinguished from reference architecture and untested production integrations. AI output is always a recommendation requiring authorized human review.

| Phase | Status | Verified evidence | Remaining work |
|---|---|---|---|
| 1 Architecture and foundations | Complete | Architecture, dependency lock, Compose, environment template, CI | Docker execution unavailable in this host |
| 2 Backend, database, CRUD | Implemented; integration pending | Canonical application lifecycle APIs; PostgreSQL runtime selected by DI; tenant RLS context; migrations and durable idempotency | Execute PostgreSQL integration suite when Docker is available |
| 3 React dashboard | Implemented core | Required analyst views, local role screen, routing/query/chart libraries, streaming assistant, citations, review/audit/evaluation pages, route code splitting | Production OIDC browser flow requires an institution identity provider |
| 4 Document ingestion | Implemented core | PDF/CSV/DOCX and DOCX tables; fixed/recursive/semantic chunking; S3 versions; SQS ingestion worker with retries | OCR and highly complex PDF table quality remain environment/document dependent |
| 5 Financial engine | Implemented core | Decimal ratios and known-answer unit tests | Additional trends and calculation persistence |
| 6 Hybrid RAG | Implemented core | Tenant-filtered PostgreSQL FTS/pgvector adapter, RRF, lexical/optional cross-encoder reranking, citations, metrics | Live PostgreSQL/cross-encoder benchmark requires Docker and the AI extra |
| 7 LangGraph workflow | Implemented core | Typed graph, specialist nodes, checkpoint contract, interrupt/resume | Production timeout policy and PostgreSQL execution tests |
| 8 Structured outputs/tools | Implemented core | Pydantic validation, Responses API adapter, allowlisted tools | Broader malformed-output fixtures |
| 9 LiteLLM/routing/cache | In progress | Real LiteLLM Router, OpenAI/Claude/Bedrock config, aliases, fallback, budgets | Live approved-provider and cost benchmark |
| 10 MCP | Implemented core | Official SDK server/client, six authenticated tenant-scoped tools and logs | Production OAuth/token verifier deployment |
| 11 Evaluation | Implemented; provider run pending | Retrieval metrics/benchmark, schema evaluation, guarded RAGAS and LangSmith runners, deterministic offline report | Provider-backed baseline requires approved credentials and explicit enablement |
| 12 Governance | Implemented core | RBAC, human review, evidence traceability, hash-chain audit | Institutional controls validation |
| 13 Deployment/monitoring | In progress | Compose includes migrations, tenant bootstrap, MinIO initialization, API, PostgreSQL worker, LocalStack/SQS, monitoring | Docker/AWS execution and rollback exercise |
| 14 End-to-end/interview | Implemented locally; deployed E2E pending | Credential-free workflow, 18 learning notes, concept matrix, walkthrough and Q&A, synthetic scale generator | Docker-based full-stack E2E remains unexecuted on this host |

## Current verification

- Ruff and strict mypy are required for every backend increment.
- Latest local verification: Ruff passed, strict mypy passed across 83 source files, and 24 tests passed.
- Backend test suite includes application lifecycle, MCP authorization, SQS acknowledgement ordering, workflow, retrieval, financial calculations, provider validation, and prompt-defense tests.
- Frontend production build validates TypeScript and Vite bundling.
- Health endpoints include `/health/live`, `/health/ready`, and the compatibility alias `/health`.
- Live mock HTTP smoke test passed: create, upload, analyze, human interrupt, evidence assistant stream, offline evaluation read, ACCEPT review, and five-event audit trail.
- No paid model or AWS calls are run by default.
- Actual generated scale fixture in this environment: 100 financial records and 100 policy chunks (seed 42); larger targets remain aspirational.
- Offline evaluation: 3 labeled cases, calculation accuracy 1.0, zero paid calls. This is a tiny deterministic fixture, not a production quality claim.

## Known production blockers

1. Legal, privacy, fair-lending, security, and model-risk approvals are not implied.
2. PostgreSQL/S3/SQS composition is implemented but cannot be executed on this host because Docker is unavailable.
3. Provider-backed evaluation numbers and aspirational scale targets must not be claimed until measured.
