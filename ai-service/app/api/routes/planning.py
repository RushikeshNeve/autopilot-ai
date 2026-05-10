from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from fastapi import APIRouter, HTTPException
from app.core.logger import get_logger
from app.schemas.goal import GoalInterpretRequest
from app.schemas.plan import (
    FinalizePlanRequest,
    FinalizePlanResponse,
    InterpretedMilestonePlanRequest,
    MilestonePlanResponse,
    PlanRevisionRequest,
    PlanRevisionResponse,
    TaskPlanRequest,
    TaskPlanResponse,
)
from app.services.llm.structured_output import StructuredOutputError
from app.services.planner.goal_interpreter import GoalInterpreterService
from app.services.planner.milestone_planner import MilestonePlannerService
from app.services.planner.task_decomposer import TaskDecomposerService
from app.services.planner.plan_finalizer import PlanFinalizerService
from app.services.evaluator.plan_critic import PlanCriticService
from app.services.evaluator.plan_reviser import PlanReviserService
from app.services.execution.router import ExecutionRouterService

router = APIRouter(prefix="/ai/planning", tags=["planning"])
logger = get_logger(__name__)

goal_interpreter_service = GoalInterpreterService()
milestone_planner_service = MilestonePlannerService()
task_decomposer_service = TaskDecomposerService()
plan_finalizer_service = PlanFinalizerService()
critic_service = PlanCriticService()
reviser_service = PlanReviserService()
execution_service = ExecutionRouterService()


@router.post("/milestones", response_model=MilestonePlanResponse)
def generate_milestones(payload: GoalInterpretRequest) -> MilestonePlanResponse:
    try:
        interpreted = goal_interpreter_service.interpret_goal(payload)
        return milestone_planner_service.generate_milestones(
            user_id=payload.user_id,
            interpreted_goal=interpreted.interpreted_goal,
        )
    except StructuredOutputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


@router.post("/milestones/from-interpreted", response_model=MilestonePlanResponse)
def generate_milestones_from_interpreted(payload: InterpretedMilestonePlanRequest) -> MilestonePlanResponse:
    try:
        logger.info(
            "planning_milestones_from_interpreted user_id=%s primary_intent=%s",
            payload.user_id,
            payload.interpreted_goal.primary_intent,
        )
        return milestone_planner_service.generate_milestones(
            user_id=payload.user_id,
            interpreted_goal=payload.interpreted_goal,
        )
    except StructuredOutputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


@router.post("/tasks", response_model=TaskPlanResponse)
def generate_tasks(payload: TaskPlanRequest) -> TaskPlanResponse:
    try:
        return task_decomposer_service.generate_tasks_for_milestone(
            user_id=payload.user_id,
            interpreted_goal=payload.interpreted_goal,
            milestone=payload.milestone,
        )
    except StructuredOutputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


@router.post("/revise", response_model=PlanRevisionResponse)
def revise_plan(payload: PlanRevisionRequest) -> PlanRevisionResponse:
    try:
        logger.info(
            "planning_revision_started user_id=%s score=%s",
            payload.user_id,
            payload.critique.overall_score,
        )
        revised_plan = reviser_service.revise_plan(
            plan=payload.plan,
            critique=payload.critique.model_dump(),
        )
        logger.info(
            "planning_revision_completed user_id=%s next_best_action=%s",
            payload.user_id,
            revised_plan.next_best_action,
        )
        return PlanRevisionResponse(plan=revised_plan)
    except StructuredOutputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


@router.post("/finalize", response_model=FinalizePlanResponse)
def finalize_plan(payload: FinalizePlanRequest) -> FinalizePlanResponse:
    start = time.perf_counter()
    try:
        logger.info(
            "planning_finalize_started user_id=%s goal_text_length=%s enable_revision=%s",
            payload.goal_request.user_id,
            len(payload.goal_request.goal_text),
            payload.enable_revision,
        )
        interpreted = payload.interpreted_goal
        if interpreted is None:
            logger.info("planning_finalize_step=goal_interpretation user_id=%s", payload.goal_request.user_id)
            interpreted = goal_interpreter_service.interpret_goal(payload.goal_request).interpreted_goal

        logger.info("planning_finalize_step=milestone_generation user_id=%s", payload.goal_request.user_id)
        milestone_result = milestone_planner_service.generate_milestones(
            user_id=payload.goal_request.user_id,
            interpreted_goal=interpreted,
        )

        all_tasks = []
        if milestone_result.milestones:
            logger.info(
                "planning_finalize_step=task_decomposition user_id=%s milestones_count=%s",
                payload.goal_request.user_id,
                len(milestone_result.milestones),
            )
            max_workers = min(4, len(milestone_result.milestones))
            tasks_by_index: dict[int, list] = {}
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_map = {
                    executor.submit(
                        task_decomposer_service.generate_tasks_for_milestone,
                        user_id=payload.goal_request.user_id,
                        interpreted_goal=interpreted,
                        milestone=milestone,
                    ): index
                    for index, milestone in enumerate(milestone_result.milestones)
                }
                for future in as_completed(future_map):
                    index = future_map[future]
                    task_result = future.result()
                    tasks_by_index[index] = task_result.tasks

            for index in range(len(milestone_result.milestones)):
                all_tasks.extend(tasks_by_index.get(index, []))

        logger.info("planning_finalize_step=plan_finalization user_id=%s tasks_count=%s", payload.goal_request.user_id, len(all_tasks))
        initial_plan = plan_finalizer_service.finalize_plan(
            user_id=payload.goal_request.user_id,
            interpreted_goal=interpreted,
            milestones=milestone_result.milestones,
            tasks=all_tasks,
        )

        critique = None
        final_plan = initial_plan
        execution = None

        if payload.enable_revision:
            logger.info("planning_finalize_step=critique user_id=%s", payload.goal_request.user_id)
            critique = critic_service.critique_plan(
                user_id=payload.goal_request.user_id,
                plan=initial_plan.model_dump(),
            )

            if critique.overall_score < 0.85:
                logger.info("planning_finalize_step=revision user_id=%s score=%s", payload.goal_request.user_id, critique.overall_score)
                final_plan = reviser_service.revise_plan(
                    plan=initial_plan,
                    critique=critique.model_dump(),
                )

            logger.info("planning_finalize_step=execution_routing user_id=%s", payload.goal_request.user_id)
            execution = execution_service.route_tasks(
                user_id=payload.goal_request.user_id,
                tasks=final_plan.tasks,
            )
        else:
            logger.info("planning_finalize_step=parallel_critique_and_execution user_id=%s", payload.goal_request.user_id)
            with ThreadPoolExecutor(max_workers=2) as executor:
                critique_future = executor.submit(
                    critic_service.critique_plan,
                    user_id=payload.goal_request.user_id,
                    plan=initial_plan.model_dump(),
                )
                execution_future = executor.submit(
                    execution_service.route_tasks,
                    user_id=payload.goal_request.user_id,
                    tasks=final_plan.tasks,
                )
            critique = critique_future.result()
            execution = execution_future.result()

        logger.info(
            "planning_finalize_completed user_id=%s elapsed_ms=%.2f",
            payload.goal_request.user_id,
            (time.perf_counter() - start) * 1000,
        )
        return FinalizePlanResponse(
            plan=final_plan,
            execution=execution,
            critique=critique,
        )

    except StructuredOutputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("planning_finalize_failed user_id=%s", payload.goal_request.user_id)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc
