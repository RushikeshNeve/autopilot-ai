"""Execution job orchestration service."""

from __future__ import annotations

from uuid import uuid4

from app.core.logger import get_logger
from app.schemas.execution import ExecutionDecision
from app.schemas.execution_job import ExecutionJob, ExecutionJobStatus
from app.schemas.task import TaskItem
from app.services.execution.job_store import JobStore
from app.services.execution.queue import ExecutionQueue

logger = get_logger(__name__)


class ExecutionService:
    """Creates execution jobs and routes them to the appropriate state."""

    def __init__(
        self,
        job_store: JobStore | None = None,
        queue: ExecutionQueue | None = None,
    ) -> None:
        self._job_store = job_store or JobStore()
        self._queue = queue or ExecutionQueue()

    @property
    def job_store(self) -> JobStore:
        return self._job_store

    @property
    def queue(self) -> ExecutionQueue:
        return self._queue

    def create_job(self, user_id: str, task: TaskItem, decision: ExecutionDecision) -> ExecutionJob:
        """Create a job and move it into the correct lifecycle state."""
        job = ExecutionJob(
            job_id=str(uuid4()),
            user_id=user_id,
            task=task,
            decision=decision,
        )

        action_mode = decision.action_mode
        logger.info(
            "creating_execution_job job_id=%s user_id=%s task_id=%s action_mode=%s",
            job.job_id,
            user_id,
            task.task_id,
            action_mode,
        )

        if action_mode == "requires_approval":
            job = job.model_copy(update={"status": ExecutionJobStatus.requires_approval})
            self._job_store.create(job)
            return job

        if action_mode in {"manual", "suggest"}:
            result = {
                "executed": False,
                "reason": decision.reason,
                "action_mode": action_mode,
            }
            job = job.model_copy(
                update={
                    "status": ExecutionJobStatus.completed,
                    "result": result,
                }
            )
            self._job_store.create(job)
            return job

        if action_mode == "auto_execute":
            job = job.model_copy(update={"status": ExecutionJobStatus.queued})
            self._job_store.create(job)
            self._queue.enqueue(job)
            logger.info("queued_execution_job job_id=%s", job.job_id)
            return job

        raise ValueError(f"Unsupported action_mode: {action_mode}")

    def mark_running(self, job_id: str) -> ExecutionJob:
        job = self._job_store.update(job_id, status=ExecutionJobStatus.running)
        logger.info("execution_job_running job_id=%s", job_id)
        return job

    def mark_completed(self, job_id: str, result: dict[str, object] | None = None) -> ExecutionJob:
        job = self._job_store.update(job_id, status=ExecutionJobStatus.completed, result=result, error=None)
        logger.info("execution_job_completed job_id=%s", job_id)
        return job

    def mark_failed(self, job_id: str, error: str) -> ExecutionJob:
        job = self._job_store.update(job_id, status=ExecutionJobStatus.failed, error=error)
        logger.error("execution_job_failed job_id=%s error=%s", job_id, error)
        return job

    def approve_job(self, job_id: str) -> ExecutionJob:
        job = self._job_store.get(job_id)
        if job is None:
            raise ValueError(f"Execution job not found: {job_id}")
        if job.status != ExecutionJobStatus.requires_approval:
            raise ValueError(f"Execution job is not awaiting approval: {job_id}")

        approved_job = self._job_store.update(job_id, status=ExecutionJobStatus.queued, error=None)
        self._queue.enqueue(approved_job)
        logger.info("execution_job_approved job_id=%s", job_id)
        return approved_job

    def reject_job(self, job_id: str, reason: str | None = None) -> ExecutionJob:
        job = self._job_store.get(job_id)
        if job is None:
            raise ValueError(f"Execution job not found: {job_id}")
        if job.status != ExecutionJobStatus.requires_approval:
            raise ValueError(f"Execution job is not awaiting approval: {job_id}")

        rejection_reason = reason or "Rejected by user"
        rejected_job = self._job_store.update(
            job_id,
            status=ExecutionJobStatus.failed,
            error=rejection_reason,
            result={
                "executed": False,
                "approved": False,
                "reason": rejection_reason,
                "action_mode": job.decision.action_mode,
            },
        )
        logger.info("execution_job_rejected job_id=%s reason=%s", job_id, rejection_reason)
        return rejected_job

    def get_job(self, job_id: str) -> ExecutionJob | None:
        return self._job_store.get(job_id)

    def list_jobs(self, status: str | None = None) -> list[ExecutionJob]:
        return self._job_store.list(status=status)
