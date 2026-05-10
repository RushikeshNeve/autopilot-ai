"""Execution job proxy routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict

from app.services.ai.ai_client import AIClient, AIServiceError

router = APIRouter(prefix="/ai/execution", tags=["executions"])

ai_client = AIClient()


class ExecutionJobReadResponse(BaseModel):
    job_id: str
    user_id: str | None = None
    task: dict[str, Any]
    decision: dict[str, Any]
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    model_config = ConfigDict(extra="ignore")


@router.get("/jobs", response_model=list[ExecutionJobReadResponse], summary="List execution jobs")
def list_execution_jobs(job_status: str | None = None) -> list[ExecutionJobReadResponse]:
    try:
        result = ai_client.list_execution_jobs(status=job_status)
        return [ExecutionJobReadResponse.model_validate(item) for item in result]
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/jobs/{job_id}", response_model=ExecutionJobReadResponse, summary="Get execution job")
def get_execution_job(job_id: str) -> ExecutionJobReadResponse:
    try:
        result = ai_client.get_execution_job(job_id)
        return ExecutionJobReadResponse.model_validate(result)
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/jobs/{job_id}/approve", response_model=ExecutionJobReadResponse, summary="Approve execution job")
def approve_execution_job(job_id: str) -> ExecutionJobReadResponse:
    try:
        result = ai_client.approve_execution_job(job_id)
        return ExecutionJobReadResponse.model_validate(result)
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


class ExecutionJobRejectRequest(BaseModel):
    reason: str | None = None


@router.post("/jobs/{job_id}/reject", response_model=ExecutionJobReadResponse, summary="Reject execution job")
def reject_execution_job(job_id: str, payload: ExecutionJobRejectRequest | None = None) -> ExecutionJobReadResponse:
    try:
        result = ai_client.reject_execution_job(job_id, reason=payload.reason if payload else None)
        return ExecutionJobReadResponse.model_validate(result)
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
