"""Background runner for asynchronous plan finalization jobs."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import HTTPException, status

from app.core.logger import get_logger
from app.db.session import get_session_factory
from app.schemas.plan import PlanFinalizeRequest
from app.services.ai.ai_client import AIServiceError
from app.services.plans.dependencies import planning_job_store
from app.services.plans.plan_service import PlanService
from app.services.websocket.dependencies import get_event_publisher

logger = get_logger(__name__)

plan_service = PlanService()


def _publish_planning_event(
    *,
    user_id: str,
    event_type: str,
    entity_type: str,
    entity_id: str,
    message: str,
    data: dict[str, Any] | None = None,
) -> None:
    """Publish a planning event from a background thread."""
    event_publisher = get_event_publisher()
    try:
        asyncio.run(
            event_publisher.publish_to_user(
                user_id,
                event_type=event_type,  # type: ignore[arg-type]
                entity_type=entity_type,
                entity_id=entity_id,
                message=message,
                data=data,
            )
        )
    except Exception:
        logger.exception("planning_websocket_publish_failed user_id=%s entity_id=%s event_type=%s", user_id, entity_id, event_type)


def run_finalize_plan_job(job_id: str) -> None:
    """Run a queued plan finalization job to completion."""
    job = planning_job_store.get(job_id)
    if job is None:
        logger.warning("planning_job_missing job_id=%s", job_id)
        return

    session_factory = get_session_factory()
    db = session_factory()
    try:
        planning_job_store.update(job_id, status="running")
        _publish_planning_event(
            user_id=str(job.user_id),
            event_type="planning_started",
            entity_type="plan",
            entity_id=job.job_id,
            message="Planning has started.",
            data={
                "job_id": job.job_id,
                "goal_id": str(job.goal_id),
                "workspace_id": str(job.workspace_id),
            },
        )

        def progress_callback(event_type: str, message: str, data: dict[str, Any] | None = None) -> None:
            _publish_planning_event(
                user_id=str(job.user_id),
                event_type=event_type,
                entity_type="plan",
                entity_id=job.job_id,
                message=message,
                data={
                    "job_id": job.job_id,
                    "goal_id": str(job.goal_id),
                    "workspace_id": str(job.workspace_id),
                    **(data or {}),
                },
            )

        payload = PlanFinalizeRequest.model_validate(job.request_payload)
        response = plan_service.finalize_plan(
            db,
            payload,
            enable_revision=False,
            progress_callback=progress_callback,
        )

        planning_job_store.update(job_id, status="completed", result=response.model_dump(mode="json"))
        _publish_planning_event(
            user_id=str(job.user_id),
            event_type="planning_completed",
            entity_type="plan",
            entity_id=job.job_id,
            message="Planning completed successfully.",
            data={
                "job_id": job.job_id,
                "goal_id": str(job.goal_id),
                "workspace_id": str(job.workspace_id),
                "plan_id": str(response.plan.id),
                "result": response.model_dump(mode="json"),
            },
        )
    except HTTPException as exc:
        logger.warning("planning_job_failed job_id=%s error=%s", job_id, exc.detail)
        planning_job_store.update(job_id, status="failed", error=str(exc.detail))
        _publish_planning_event(
            user_id=str(job.user_id),
            event_type="planning_progress",
            entity_type="plan",
            entity_id=job.job_id,
            message="Planning failed.",
            data={
                "job_id": job.job_id,
                "goal_id": str(job.goal_id),
                "workspace_id": str(job.workspace_id),
                "error": str(exc.detail),
                "status": "failed",
            },
        )
    except AIServiceError as exc:
        logger.warning("planning_job_ai_failed job_id=%s error=%s", job_id, exc)
        planning_job_store.update(job_id, status="failed", error=str(exc))
        _publish_planning_event(
            user_id=str(job.user_id),
            event_type="planning_progress",
            entity_type="plan",
            entity_id=job.job_id,
            message="Planning failed.",
            data={
                "job_id": job.job_id,
                "goal_id": str(job.goal_id),
                "workspace_id": str(job.workspace_id),
                "error": str(exc),
                "status": "failed",
            },
        )
    except Exception as exc:
        logger.exception("planning_job_unexpected_failure job_id=%s", job_id)
        planning_job_store.update(job_id, status="failed", error=str(exc))
        _publish_planning_event(
            user_id=str(job.user_id),
            event_type="planning_progress",
            entity_type="plan",
            entity_id=job.job_id,
            message="Planning failed.",
            data={
                "job_id": job.job_id,
                "goal_id": str(job.goal_id),
                "workspace_id": str(job.workspace_id),
                "error": str(exc),
                "status": "failed",
            },
        )
    finally:
        db.close()
