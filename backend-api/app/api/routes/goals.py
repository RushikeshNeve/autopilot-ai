"""Goal routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.goal import GoalCreateRequest, GoalCreateResponse, GoalRead
from app.schemas.plan import PlanFinalizeRequest
from app.services.goals.goal_service import GoalService
from app.services.plans.planning_job_service import PlanningJobService

router = APIRouter(prefix="/goals", tags=["goals"])

goal_service = GoalService()
planning_job_service = PlanningJobService()


@router.post(
    "",
    response_model=GoalCreateResponse,
    summary="Create goal",
    description="Create a goal record and optionally trigger planning through ai-service.",
)
def create_goal(
    payload: GoalCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> GoalCreateResponse:
    try:
        goal = goal_service.create_goal(db, payload)
        if payload.trigger_planning:
            job = planning_job_service.create_job(
                db,
                PlanFinalizeRequest(goal_id=goal.id, submit_execution_jobs=False),
            )
            # Run the long AI planning flow after the response is returned.
            background_tasks.add_task(planning_job_service.start_job, job.job_id)
        return GoalCreateResponse(
            goal=GoalRead.model_validate(goal),
            plan=None,
            planning_job_id=job.job_id if payload.trigger_planning else None,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{goal_id}",
    response_model=GoalRead,
    summary="Get goal",
    description="Fetch a stored goal by identifier.",
)
def get_goal(goal_id: UUID, db: Session = Depends(get_db)) -> GoalRead:
    try:
        return GoalRead.model_validate(goal_service.get_goal(db, goal_id))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
