# Implementation progress

Updated: 2026-10-21

## 2026-10-30 structural refactor

- Split the React dashboard into seven pages, reusable components, hooks, API service, and shared types.
- Split the versioned API into cases, documents, underwriting, reviews/audit, and policy routers without changing endpoint contracts.
- Split LangGraph nodes into seven specialized agent modules; `graph.py` now only composes the durable workflow.
- Split hybrid retrieval into models, embeddings, fusion, reranking, citation, and pipeline stages while preserving compatibility exports.
- Added explicit token-budget and Decimal inference-cost modules.
- Added a version-aware compliance policy catalog and prompt-injection evidence delimiter.
- Post-refactor checks: Ruff passed, mypy passed across 61 source files, 12 tests passed at 87% coverage, and the frontend production build passed.

| Phase | Status | Evidence / limitation |
|---|---|---|
| 1 Architecture/repository | Complete | `docs/`, pinned `pyproject.toml`, `uv.lock` |
| 2 Core backend | Implemented | FastAPI contracts, strict schemas, ORM model, Alembic; PostgreSQL runtime verification requires Docker |
| 3 Ingestion/RAG | Implemented core | PDF/CSV extraction, chunk provenance, hybrid fusion/reranking, pgvector/FTS migration; live 15M-scale benchmark not claimed |
| 4 Multi-agent workflow | Implemented | Real `StateGraph`, checkpointing contract, bounded verification, human interrupt/resume |
| 5 Integration | Partial | Credential-free async runtime works; SQS worker and cloud object adapter require integration environment |
| 6 Evaluation/performance | In progress | Offline datasets/tests added; paid evaluation disabled |
| 7 Frontend/observability | In progress | Prometheus instrumentation; dashboard assets pending verification |
| 8 AWS/CI/CD | In progress | Deployment assets require Docker/Terraform binaries and AWS operator approval |
| 9 Hardening | In progress | Automated checks run continuously; record exact results below |

## Verification log

- Python 3.12.15 installed through `uv`.
- Dependency lock generated with `uv 0.13.1`.
- Ruff formatting/lint: passed (2026-10-21).
- mypy strict mode: passed across 33 source files (2026-10-21).
- pytest: 10 passed; 87% statement coverage before final dependency refresh (2026-10-21).
- Frontend TypeScript/Vite production build: passed (2026-10-21).
- Offline evaluation: 3/3 deterministic calculation fixtures passed; zero paid calls.
- `pip-audit`: no known third-party vulnerabilities after upgrading patched 2026 releases; the local unpublished package is skipped by design.
- Terraform 1.14.0 was downloaded to the approved temporary directory: `fmt -check`, provider initialization, and `validate` passed. No plan/apply or paid infrastructure was run.
- Docker is not installed in this execution environment; image builds and Compose startup cannot be reported as validated here.
- No paid API or AWS calls were made.

## Production blockers

1. Obtain legal, privacy, fair-lending, information-security, model-risk, and institution policy approvals.
2. Validate OIDC claims/role mapping against the institution identity provider.
3. Run PostgreSQL/RLS, pgvector, Redis, S3 Object Lock, SQS redrive, backup/restore, and disaster-recovery integration tests in an AWS-like environment.
4. The deployment composition now selects the PostgreSQL/S3/SQS runtime and an idempotent durable worker; run its integration, load, and chaos tests in a Docker/AWS environment.
5. Validate model/provider behavior and evaluation thresholds using approved, representative, non-production or properly governed data.
