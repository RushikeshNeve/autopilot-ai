"""Plan routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.plan import (
    PlanFinalizeJobCreateResponse,
    PlanFinalizeJobRead,
    PlanFinalizeRequest,
    PlanFinalizeResponse,
    PlanRead,
)
from app.services.plans.planning_job_service import PlanningJobService
from app.services.plans.plan_service import PlanService

router = APIRouter(prefix="/plans", tags=["plans"])

plan_service = PlanService()
planning_job_service = PlanningJobService()


@router.post(
    "/finalize",
    response_model=PlanFinalizeResponse,
    summary="Finalize plan",
    description="Call ai-service to interpret the goal, generate a plan, and optionally submit execution jobs.",
)
def finalize_plan(payload: PlanFinalizeRequest, db: Session = Depends(get_db)) -> PlanFinalizeResponse:
    try:
        return plan_service.finalize_plan(db, payload)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post(
    "/finalize/async",
    response_model=PlanFinalizeJobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue plan finalization",
    description="Create an asynchronous plan job and process it in the background while the frontend listens for websocket updates.",
)
def finalize_plan_async(
    payload: PlanFinalizeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> PlanFinalizeJobCreateResponse:
    try:
        job = planning_job_service.create_job(db, payload)
        background_tasks.add_task(planning_job_service.start_job, job.job_id)
        return job
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/jobs/{job_id}",
    response_model=PlanFinalizeJobRead,
    summary="Get plan job",
    description="Fetch the status of an asynchronous plan finalization job.",
)
def get_plan_job(job_id: str) -> PlanFinalizeJobRead:
    try:
        return planning_job_service.get_job(job_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{plan_id}",
    response_model=PlanRead,
    summary="Get plan",
    description="Fetch a stored plan by identifier.",
)
def get_plan(plan_id: UUID, db: Session = Depends(get_db)) -> PlanRead:
    try:
        plan = plan_service.get_plan(db, plan_id)
        return plan_service._to_plan_read(plan, execution_jobs=[])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post(
    "/{plan_id}/execution-jobs",
    response_model=PlanRead,
    summary="Create execution jobs from a plan",
    description="Use the stored plan decisions to create execution jobs for auto-execute and approval-required tasks.",
)
def create_execution_jobs(plan_id: UUID, db: Session = Depends(get_db)) -> PlanRead:
    try:
        return plan_service.create_execution_jobs_for_plan(db, plan_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
