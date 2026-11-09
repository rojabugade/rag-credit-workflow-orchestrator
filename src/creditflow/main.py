import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text

from creditflow.api.middleware.request_context import RequestContextMiddleware
from creditflow.api.v1.router import router
from creditflow.core.config import get_settings
from creditflow.core.errors import CreditFlowError
from creditflow.db.session import engine
from creditflow.observability.tracing import configure_tracing
from creditflow.schemas.common import ErrorDetail, ErrorResponse


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ]
    )
    yield


app = FastAPI(
    title="CreditFlow AI",
    version="0.1.0",
    description="Evidence-backed underwriting recommendations. The AI never makes final credit decisions.",
    lifespan=lifespan,
)

app.add_middleware(RequestContextMiddleware)  # Adds processing around incoming HTTP requests
app.include_router(router)  # Adds/Registers the API endpoint to the FastAPI application
configure_tracing(
    app, endpoint=get_settings().otel_exporter_otlp_endpoint
)  # Sets up request tracing for observability


@app.exception_handler(CreditFlowError)
async def application_error(request: Request, exc: CreditFlowError) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorDetail(
            code=exc.code,
            message=exc.message,
            request_id=getattr(request.state, "request_id", "unknown"),
            details=exc.details,
        )
    )
    return JSONResponse(status_code=exc.status_code, content=body.model_dump(mode="json"))


@app.exception_handler(ValueError)
async def validation_error(request: Request, exc: ValueError) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorDetail(
            code="invalid_request",
            message=str(exc),
            request_id=getattr(request.state, "request_id", "unknown"),
        )
    )
    return JSONResponse(status_code=422, content=body.model_dump(mode="json"))


@app.get("/health/live", include_in_schema=False)  # Check if the application is alive
async def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/health/ready", include_in_schema=False
)  # Check if the application is ready to serve requests
async def ready() -> JSONResponse:
    settings = get_settings()
    if settings.runtime_backend == "postgres":
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except Exception:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "dependency": "postgres"},
            )
    return JSONResponse(
        content={
            "status": "ready",
            "mode": "mock" if settings.mock_llm_mode else "live",
        }
    )


@app.get("/health", include_in_schema=False)
async def health() -> JSONResponse:
    """Compatibility alias for infrastructure that expects a single health endpoint."""
    return await ready()


@app.get("/metrics", include_in_schema=False)
async def metrics(request: Request) -> Response:
    settings = get_settings()
    if (
        settings.env not in {"local", "test"}
        and request.headers.get("x-internal-metrics-token") is None
    ):
        return Response(status_code=404)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
