"""Plan orchestration logic."""

from __future__ import annotations

from typing import Any
from collections.abc import Callable
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.db.models import Goal, Plan, Workspace
from app.schemas.plan import ExecutionDecision, ExecutionJobSummary, PlanFinalizeRequest, PlanFinalizeResponse, PlanRead
from app.services.ai.ai_client import AIClient, AIServiceError

logger = get_logger(__name__)


class PlanService:
    """Plan finalization and execution job orchestration."""

    def __init__(self, ai_client: AIClient | None = None) -> None:
        self._ai_client = ai_client or AIClient()

    def finalize_plan(
        self,
        db: Session,
        payload: PlanFinalizeRequest,
        *,
        enable_revision: bool | None = None,
        progress_callback: Callable[[str, str, dict[str, Any] | None], None] | None = None,
    ) -> PlanFinalizeResponse:
        goal = db.get(Goal, payload.goal_id)
        if goal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        workspace = db.get(Workspace, goal.workspace_id)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        def emit(event_type: str, message: str, data: dict[str, Any] | None = None) -> None:
            if progress_callback is not None:
                progress_callback(event_type, message, data)

        interpreted_goal = goal.interpreted_goal
        if interpreted_goal is None:
            emit(
                "planning_progress",
                "Interpreting goal",
                {"goal_id": str(goal.id), "workspace_id": str(goal.workspace_id)},
            )
            interpreted_response = self._ai_client.interpret_goal(
                {
                    "user_id": str(workspace.user_id),
                    "goal_text": goal.goal_text,
                    "constraints": goal.constraints,
                    "domain_hint": goal.domain_hint,
                }
            )
            interpreted_goal = interpreted_response.get("interpreted_goal")
            goal = self._persist_goal_ai_response(
                db,
                goal,
                status_value="interpreted",
                interpreted_goal=interpreted_goal,
                ai_response=interpreted_response,
            )
            emit(
                "planning_progress",
                "Goal interpreted",
                {"goal_id": str(goal.id), "workspace_id": str(goal.workspace_id)},
            )
        else:
            emit(
                "planning_progress",
                "Using stored interpreted goal",
                {"goal_id": str(goal.id), "workspace_id": str(goal.workspace_id)},
            )

        try:
            emit(
                "planning_progress",
                "Generating structured plan in stages",
                {"goal_id": str(goal.id), "workspace_id": str(goal.workspace_id)},
            )
            ai_response = self._ai_client.finalize_plan(
                {
                    "goal_request": {
                        "user_id": str(workspace.user_id),
                    "goal_text": goal.goal_text,
                    "constraints": goal.constraints,
                    "domain_hint": goal.domain_hint,
                }
                },
                enable_revision=enable_revision,
                interpreted_goal=interpreted_goal,
                progress_callback=progress_callback,
            )
        except AIServiceError as exc:
            logger.exception("plan_finalize_failed goal_id=%s", goal.id)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

        plan = self._persist_plan(db, goal, ai_response, submit_execution_jobs=payload.submit_execution_jobs)
        execution_jobs: list[ExecutionJobSummary] = []
        if payload.submit_execution_jobs:
            emit(
                "planning_progress",
                "Submitting execution jobs",
                {"goal_id": str(goal.id), "workspace_id": str(goal.workspace_id), "plan_id": str(plan.id)},
            )
            execution_jobs = self._submit_execution_jobs(
                user_id=str(workspace.user_id),
                plan_response=ai_response,
            )
            plan.response_payload = {
                **(plan.response_payload or {}),
                "execution_jobs": [job.model_dump() for job in execution_jobs],
            }
            db.add(plan)
            db.commit()
            db.refresh(plan)
            emit(
                "planning_progress",
                "Execution jobs submitted",
                {
                    "goal_id": str(goal.id),
                    "workspace_id": str(goal.workspace_id),
                    "plan_id": str(plan.id),
                    "execution_jobs": len(execution_jobs),
                },
            )

        plan_read = self._to_plan_read(plan, execution_jobs=execution_jobs)
        emit(
            "planning_progress",
            "Plan persisted",
            {"goal_id": str(goal.id), "workspace_id": str(goal.workspace_id), "plan_id": str(plan.id)},
        )
        return PlanFinalizeResponse(plan=plan_read, raw_ai_response=ai_response)

    def create_execution_jobs_for_plan(self, db: Session, plan_id: UUID) -> PlanRead:
        plan = self.get_plan(db, plan_id)
        goal = db.get(Goal, plan.goal_id)
        if goal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        workspace = db.get(Workspace, goal.workspace_id)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        if isinstance(plan.response_payload, dict):
            existing_jobs = plan.response_payload.get("execution_jobs", [])
            if isinstance(existing_jobs, list) and existing_jobs:
                return self._to_plan_read(
                    plan,
                    execution_jobs=[
                        ExecutionJobSummary.model_validate(item)
                        for item in existing_jobs
                        if isinstance(item, dict)
                    ],
                )

        if not isinstance(plan.response_payload, dict):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plan has no stored response payload")

        execution_decisions = plan.execution_decisions or []
        plan_response = {
            "plan": plan.response_payload,
            "execution": {"decisions": execution_decisions},
        }
        execution_jobs = self._submit_execution_jobs(
            user_id=str(workspace.user_id),
            plan_response=plan_response,
        )

        plan.response_payload = {
            **plan.response_payload,
            "execution_jobs": [job.model_dump() for job in execution_jobs],
        }
        db.add(plan)
        db.commit()
        db.refresh(plan)

        return self._to_plan_read(plan, execution_jobs=execution_jobs)

    def get_plan(self, db: Session, plan_id: UUID) -> Plan:
        plan = db.get(Plan, plan_id)
        if plan is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        return plan

    def _persist_goal_ai_response(
        self,
        db: Session,
        goal: Goal,
        *,
        status_value: str,
        interpreted_goal: dict[str, Any] | None,
        ai_response: dict[str, Any],
    ) -> Goal:
        goal.status = status_value
        goal.interpreted_goal = interpreted_goal
        goal.ai_response = ai_response
        db.add(goal)
        db.commit()
        db.refresh(goal)
        return goal

    def _persist_plan(
        self,
        db: Session,
        goal: Goal,
        ai_response: dict[str, Any],
        *,
        submit_execution_jobs: bool,
    ) -> Plan:
        plan_payload = ai_response.get("plan", {})
        execution_payload = ai_response.get("execution", {}) or {}
        execution_decisions = execution_payload.get("decisions", []) or []
        approval_ready = [
            decision
            for decision in execution_decisions
            if decision.get("action_mode") in {"auto_execute", "requires_approval"}
        ]

        plan = Plan(
            goal_id=goal.id,
            status="completed",
            request_payload={
                "goal_id": str(goal.id),
                "workspace_id": str(goal.workspace_id),
                "submit_execution_jobs": submit_execution_jobs,
            },
            response_payload=plan_payload,
            execution_decisions=execution_decisions,
            approval_ready_execution_decisions=approval_ready,
        )
        db.add(plan)
        goal.status = "planned"
        db.add(goal)
        db.commit()
        db.refresh(plan)
        db.refresh(goal)
        return plan

    def _submit_execution_jobs(self, user_id: str, plan_response: dict[str, Any]) -> list[ExecutionJobSummary]:
        execution_payload = plan_response.get("execution", {}) or {}
        decisions = execution_payload.get("decisions", []) or []
        plan_payload = plan_response.get("plan", {}) or {}
        tasks = plan_payload.get("tasks", []) or []
        tasks_by_id = {task.get("task_id"): task for task in tasks if task.get("task_id")}

        jobs: list[ExecutionJobSummary] = []
        for decision in decisions:
            if decision.get("action_mode") not in {"auto_execute", "requires_approval"}:
                continue
            task_id = decision.get("task_id")
            task = tasks_by_id.get(task_id)
            if task is None:
                continue

            try:
                result = self._ai_client.submit_execution_job(
                    {
                        "user_id": user_id,
                        "task": task,
                        "decision": decision,
                    }
                )
                jobs.append(
                    ExecutionJobSummary(
                        job_id=str(result.get("job_id", "")),
                        status=str(result.get("status", "")),
                        task_id=str(task_id),
                        action_mode=str(decision.get("action_mode", "")),
                    )
                )
            except AIServiceError as exc:
                logger.warning("execution_job_submit_failed task_id=%s error=%s", task_id, exc)

        return jobs

    def _to_plan_read(self, plan: Plan, execution_jobs: list[ExecutionJobSummary]) -> PlanRead:
        stored_execution_jobs = execution_jobs
        if not stored_execution_jobs and isinstance(plan.response_payload, dict):
            raw_jobs = plan.response_payload.get("execution_jobs", [])
            stored_execution_jobs = [
                ExecutionJobSummary.model_validate(item) for item in raw_jobs if isinstance(item, dict)
            ]
        return PlanRead(
            id=plan.id,
            goal_id=plan.goal_id,
            status=plan.status,
            request_payload=plan.request_payload,
            response_payload=plan.response_payload,
            execution_decisions=[ExecutionDecision.model_validate(item) for item in plan.execution_decisions],
            approval_ready_execution_decisions=[
                ExecutionDecision.model_validate(item) for item in plan.approval_ready_execution_decisions
            ],
            execution_jobs=stored_execution_jobs,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )
