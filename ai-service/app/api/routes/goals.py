"""Goal-related routes."""

from fastapi import APIRouter, HTTPException

from app.core.logger import get_logger
from app.schemas.goal import GoalInterpretRequest, GoalInterpretResponse
from app.services.llm.structured_output import StructuredOutputError
from app.services.planner.goal_interpreter import GoalInterpreterService

router = APIRouter(prefix="/ai/goals", tags=["goals"])
logger = get_logger(__name__)

goal_interpreter_service = GoalInterpreterService()


@router.post("/interpret", response_model=GoalInterpretResponse)
def interpret_goal(payload: GoalInterpretRequest) -> GoalInterpretResponse:
    try:
        logger.info(
            "goal_interpret_request_received user_id=%s goal_text_length=%s constraints_count=%s domain_hint=%s",
            payload.user_id,
            len(payload.goal_text),
            len(payload.constraints),
            payload.domain_hint or "none",
        )
        return goal_interpreter_service.interpret_goal(payload)
    except StructuredOutputError as exc:
        logger.warning(
            "goal_interpret_structured_output_error user_id=%s error=%s",
            payload.user_id,
            exc,
        )
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(
            "goal_interpret_unexpected_error user_id=%s",
            payload.user_id,
        )
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc
