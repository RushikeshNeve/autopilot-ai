"""Execution job API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from app.schemas.execution_job import ExecutionJob, ExecutionJobStatus
from app.services.execution.dependencies import get_execution_service
from app.services.execution.execution_service import ExecutionService
from app.services.execution.job_store import JobNotFoundError
from app.schemas.execution import ExecutionDecision
from app.schemas.task import TaskItem

router = APIRouter(prefix="/ai/execution/jobs", tags=["execution-jobs"])


class ExecutionJobSubmitRequest(BaseModel):
    user_id: str
    task: TaskItem
    decision: ExecutionDecision


class ExecutionJobSubmitResponse(BaseModel):
    job_id: str
    status: ExecutionJobStatus

    model_config = ConfigDict(use_enum_values=True)


class ExecutionJobStatusResponse(BaseModel):
    job_id: str
    status: ExecutionJobStatus
    result: dict[str, Any] | None = None
    error: str | None = None

    model_config = ConfigDict(use_enum_values=True)


class ExecutionJobReadResponse(ExecutionJob):
    """Full execution job record."""

    model_config = ConfigDict(use_enum_values=True)


@router.get("", response_model=list[ExecutionJobReadResponse], summary="List execution jobs")
def list_execution_jobs(
    job_status: ExecutionJobStatus | None = None,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> list[ExecutionJobReadResponse]:
    try:
        jobs = execution_service.list_jobs(status=job_status.value if job_status else None)
        return [ExecutionJobReadResponse.model_validate(job.model_dump()) for job in jobs]
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("", response_model=ExecutionJobSubmitResponse, status_code=status.HTTP_201_CREATED)
def submit_execution_job(
    payload: ExecutionJobSubmitRequest,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> ExecutionJobSubmitResponse:
    try:
        job = execution_service.create_job(
            user_id=payload.user_id,
            task=payload.task,
            decision=payload.decision,
        )
        return ExecutionJobSubmitResponse(job_id=job.job_id, status=job.status)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/{job_id}", response_model=ExecutionJobReadResponse)
def get_execution_job(
    job_id: str,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> ExecutionJobReadResponse:
    try:
        job: ExecutionJob | None = execution_service.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution job not found")
        return ExecutionJobReadResponse.model_validate(job.model_dump())
    except HTTPException:
        raise
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution job not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/{job_id}/approve", response_model=ExecutionJobReadResponse)
def approve_execution_job(
    job_id: str,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> ExecutionJobReadResponse:
    try:
        job = execution_service.approve_job(job_id)
        return ExecutionJobReadResponse.model_validate(job.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution job not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


class ExecutionJobRejectRequest(BaseModel):
    reason: str | None = None


@router.post("/{job_id}/reject", response_model=ExecutionJobReadResponse)
def reject_execution_job(
    job_id: str,
    payload: ExecutionJobRejectRequest | None = None,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> ExecutionJobReadResponse:
    try:
        job = execution_service.reject_job(job_id, reason=payload.reason if payload else None)
        return ExecutionJobReadResponse.model_validate(job.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution job not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
