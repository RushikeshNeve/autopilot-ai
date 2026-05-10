"""Evaluation routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.evaluation import CritiqueRequest, CritiqueResponse
from app.services.evaluator.plan_critic import PlanCriticService
from app.services.llm.structured_output import StructuredOutputError

router = APIRouter(prefix="/ai/evaluation", tags=["evaluation"])

plan_critic_service = PlanCriticService()


@router.post("/critique", response_model=CritiqueResponse)
def critique_plan(payload: CritiqueRequest) -> CritiqueResponse:
    try:
        critique = plan_critic_service.critique_plan(
            user_id=payload.user_id,
            plan=payload.plan,
        )
        return CritiqueResponse(critique=critique)
    except StructuredOutputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

