"""Entry point for the ai-service application."""

import time

from fastapi import FastAPI, Request
from fastapi.responses import Response

from app.api.routes.goals import router as goals_router
from app.api.routes.integrations import router as integrations_router
from app.api.routes.health import router as health_router
from app.api.routes.execution_jobs import router as execution_jobs_router
from app.api.routes.rag import router as rag_router
from app.api.routes.planning import router as planning_router
from app.api.routes.evaluation import router as evaluation_router
from app.api.routes.execution import router as execution_router
from app.core.config import get_settings
from app.core.logger import get_logger, setup_logger
from app.services.execution.dependencies import get_execution_service, get_execution_worker

logger = get_logger(__name__)

setup_logger()
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(health_router)
app.include_router(goals_router)
app.include_router(integrations_router)
app.include_router(planning_router)
app.include_router(evaluation_router)
app.include_router(execution_router)
app.include_router(execution_jobs_router)
app.include_router(rag_router)


@app.on_event("startup")
def start_execution_worker() -> None:
    worker = get_execution_worker()
    worker.start()
    execution_service = get_execution_service()
    for job in execution_service.job_store.list():
        if job.status in {"queued", "running"}:
            execution_service.queue.enqueue(job)


@app.on_event("shutdown")
def stop_execution_worker() -> None:
    get_execution_worker().stop()


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next) -> Response:
    start = time.perf_counter()
    logger.info("request_started method=%s path=%s", request.method, request.url.path)
    try:
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request_finished method=%s path=%s status_code=%s elapsed_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
    except Exception:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "request_failed method=%s path=%s elapsed_ms=%.2f",
            request.method,
            request.url.path,
            elapsed_ms,
        )
        raise
