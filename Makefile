.PHONY: install format lint type test eval run web
install:
	uv sync --frozen --extra dev
format:
	uv run ruff format .
lint:
	uv run ruff format --check .
	uv run ruff check .
type:
	uv run mypy src
test:
	uv run pytest --cov=creditflow
eval:
	uv run python evals/run_evaluation.py
run:
	uv run uvicorn creditflow.main:app --reload
web:
	npm --prefix web run dev
