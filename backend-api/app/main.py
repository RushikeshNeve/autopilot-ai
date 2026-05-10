"""FastAPI application bootstrap for backend-api."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading

from app.api.routes.auth import router as auth_router
from app.api.routes.goals import router as goals_router
from app.api.routes.integrations import router as integrations_router
from app.api.routes.executions import router as executions_router
from app.api.routes.health import router as health_router
from app.api.routes.rag import router as rag_router
from app.api.routes.plans import router as plans_router
from app.api.routes.websocket import router as websocket_router
from app.core.config import get_settings
from app.core.logger import get_logger, setup_logger
from app.db.models import User  # noqa: F401
from app.api.routes.workspaces import router as workspaces_router
from app.db.postgres import Base
from app.db.session import get_engine
from app.services.plans.dependencies import planning_job_store
from app.services.plans.planning_job_service import PlanningJobService

setup_logger()
settings = get_settings()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    description=(
        "Application orchestration API for the AI platform. "
        "This service manages authentication, workspaces, goals, plans, and realtime updates, "
        "while delegating AI-heavy work to the separate ai-service."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "health", "description": "Liveness and readiness checks for service monitoring."},
        {"name": "auth", "description": "User authentication and JWT issuance."},
        {"name": "workspaces", "description": "Workspace creation and lookup."},
        {"name": "goals", "description": "Goal creation and planning orchestration."},
        {"name": "plans", "description": "Plan finalization and execution coordination."},
        {"name": "executions", "description": "Execution job creation and tracking."},
        {"name": "approvals", "description": "Approval-gated execution workflows."},
        {"name": "rag", "description": "Document ingestion into the reusable RAG layer."},
        {"name": "websocket", "description": "Authenticated realtime progress updates."},
    ],
)

allowed_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(workspaces_router)
app.include_router(goals_router)
app.include_router(integrations_router)
app.include_router(plans_router)
app.include_router(executions_router)
app.include_router(rag_router)
app.include_router(websocket_router)


def _resume_planning_job(job_id: str) -> None:
    planning_job_service = PlanningJobService()
    planning_job_service.start_job(job_id)


@app.on_event("startup")
def on_startup() -> None:
    """Initialize database tables for the foundation phase."""
    logger.info("backend_api_starting app_env=%s", settings.app_env)
    Base.metadata.create_all(bind=get_engine())
    for job in planning_job_store.list():
        if job.status in {"queued", "running"}:
            threading.Thread(target=_resume_planning_job, args=(job.job_id,), daemon=True).start()
