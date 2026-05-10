"""Application service for asynchronous plan jobs."""

from __future__ import annotations

from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Goal, Workspace
from app.schemas.plan import PlanFinalizeJobCreateResponse, PlanFinalizeJobRead, PlanFinalizeRequest
from app.services.plans.dependencies import planning_job_store
from app.services.plans.planning_job_runner import run_finalize_plan_job


class PlanningJobService:
    """Manage asynchronous plan finalization jobs."""

    def create_job(self, db: Session, payload: PlanFinalizeRequest) -> PlanFinalizeJobCreateResponse:
        goal = db.get(Goal, payload.goal_id)
        if goal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        workspace = db.get(Workspace, goal.workspace_id)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        job_id = str(uuid4())
        planning_job_store.create(
            job_id=job_id,
            goal_id=goal.id,
            workspace_id=goal.workspace_id,
            user_id=workspace.user_id,
            request_payload=payload.model_dump(mode="json"),
        )
        return PlanFinalizeJobCreateResponse(job_id=job_id, status="queued")

    def get_job(self, job_id: str) -> PlanFinalizeJobRead:
        job = planning_job_store.get(job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan job not found")
        return PlanFinalizeJobRead.model_validate(job.model_dump())

    def start_job(self, job_id: str) -> None:
        run_finalize_plan_job(job_id)
