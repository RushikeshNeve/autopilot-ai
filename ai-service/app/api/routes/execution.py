from fastapi import APIRouter, HTTPException
from app.schemas.execution import ExecutionRequest, ExecutionResponse
from app.services.execution.router import ExecutionRouterService
from app.services.llm.structured_output import StructuredOutputError

router = APIRouter(prefix="/ai/execution", tags=["execution"])

execution_router_service = ExecutionRouterService()


@router.post("/route", response_model=ExecutionResponse)
def route_tasks(payload: ExecutionRequest) -> ExecutionResponse:
    try:
        return execution_router_service.route_tasks(
            user_id=payload.user_id,
            tasks=payload.tasks,
        )
    except StructuredOutputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc