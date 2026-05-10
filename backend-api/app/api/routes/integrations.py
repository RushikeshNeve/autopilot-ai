"""Integration status proxy routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.integration import IntegrationStatus
from app.services.ai.ai_client import AIClient, AIServiceError

router = APIRouter(prefix="/ai/integrations", tags=["integrations"])

ai_client = AIClient()


@router.get("", response_model=list[IntegrationStatus], summary="List integration status")
def list_integrations() -> list[IntegrationStatus]:
    try:
        result = ai_client.list_integrations()
        return [IntegrationStatus.model_validate(item) for item in result]
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
