# CreditFlow AI

Production-oriented, human-supervised commercial credit analysis. CreditFlow extracts evidence, performs deterministic financial calculations, retrieves versioned policies, verifies citations, and produces a **recommendation** for an authorized human underwriter. It never approves or denies credit autonomously.

All checked-in examples are synthetic. Example policy thresholds are illustrative internal rules—not legal requirements or universal lending standards.

## Quick start (no paid API key)

Prerequisites: Python 3.12 and `uv`. Docker is optional for the lightweight local mode.

```bash
cp .env.example .env                 # PowerShell: Copy-Item .env.example .env
uv sync --extra dev
uv run uvicorn creditflow.main:app --reload
```

Open API docs at <http://localhost:8000/docs>. The isolated local auth mode creates a synthetic analyst principal. It is rejected by staging/production configuration validation.

Full local stack (when Docker is installed):

```bash
docker compose up --build -d
docker compose exec api python scripts/seed.py
```

Compose automatically runs Alembic migrations, provisions the fixed synthetic local tenant,
creates the private MinIO bucket, starts the PostgreSQL-backed API, and starts the SQS worker.
The lightweight non-Docker command continues to use the process-local mock runtime by design.

## Demonstration

With the mock API running, the repeatable end-to-end check covers health, application creation,
CSV upload, analysis, the streaming assistant, offline evaluation, human review, and audit:

```bash
uv run python scripts/smoke_mock_e2e.py
```

The equivalent manual requests are:

```bash
# Create case (save the returned id)
curl -X POST http://localhost:8000/api/v1/cases \
  -H "Content-Type: application/json" -H "Idempotency-Key: demo-case-a" \
  -d '{"borrower_name":"Synthetic Stable LLC","requested_amount":"500000.00","currency":"USD","jurisdiction":"US"}'

curl -X POST http://localhost:8000/api/v1/cases/CASE_ID/documents \
  -F "file=@sample_data/documents/case_a_financials.csv;type=text/csv"

curl -X POST http://localhost:8000/api/v1/cases/CASE_ID/analyze \
  -H "Idempotency-Key: demo-analysis-a"

curl http://localhost:8000/api/v1/jobs/JOB_ID
curl http://localhost:8000/api/v1/cases/CASE_ID/analysis
curl -X POST http://localhost:8000/api/v1/cases/CASE_ID/review \
  -H "Content-Type: application/json" \
  -d '{"action":"ACCEPT","rationale":"Evidence and calculations reviewed by an authorized analyst.","expected_case_version":3}'
curl http://localhost:8000/api/v1/cases/CASE_ID/audit
```

Cases B and C use `case_b_financials.csv` and `case_c_incomplete.csv`. The workflow should identify elevated risk for B and request missing information for C.

## Checks

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest --cov=creditflow
npm --prefix frontend ci && npm --prefix frontend run build
terraform -chdir=infra/terraform fmt -check && terraform -chdir=infra/terraform validate
```

Paid RAGAS/provider evaluations are never run by default. Use `uv sync --extra eval` and explicitly set provider credentials before `uv run python evals/run_evaluation.py --provider-backed`.

## Real providers

Set `CREDITFLOW_MOCK_LLM_MODE=false` and `CREDITFLOW_OPENAI_API_KEY`. `OpenAIResponsesProvider` uses `AsyncOpenAI.responses.parse` (Responses API structured outputs), checks incomplete/refusal states, and validates into Pydantic. No Assistants API is used. LiteLLM/Anthropic are optional routing targets and must be enabled by deployment policy.

## Documentation

- [Architecture](docs/architecture.md) · [Database](docs/database.md) · [Workflow](docs/langgraph.md)
- [Retrieval](docs/retrieval.md) · [Security](docs/security.md) · [Deployment](docs/deployment.md)
- [Performance](docs/performance.md) · [Runbook](docs/runbook.md) · [Interview guide](docs/interview-guide.md)
- [Progress and verified limitations](PROJECT_PROGRESS.md)

## Important readiness note

The repository contains deployable architecture and a complete credential-free vertical slice. Do not treat it as approved for real lending. Fair-lending review, privacy/legal approval, model-risk validation, penetration testing, disaster-recovery testing, controls testing, and institution-specific policy validation are mandatory before production use. See `PROJECT_PROGRESS.md` for exact environment verification results and blockers.
