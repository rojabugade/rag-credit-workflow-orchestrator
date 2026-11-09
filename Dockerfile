# syntax=docker/dockerfile:1.7
FROM python:3.12.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/app/.venv/bin:$PATH
RUN groupadd --system creditflow && useradd --system --gid creditflow --home /app creditflow
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./
COPY scripts ./scripts
COPY sample_data ./sample_data
RUN uv sync --frozen --no-dev --no-editable && chown -R creditflow:creditflow /app
USER creditflow
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"]

FROM base AS api
CMD ["uvicorn", "creditflow.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

FROM base AS worker
CMD ["python", "-m", "creditflow.workers.sqs_worker"]
