"""Background worker for execution jobs."""

from __future__ import annotations

import threading
from typing import Any

from app.core.logger import get_logger
from app.schemas.execution_job import ExecutionJob, ExecutionJobStatus
from app.services.execution.integration_resolver import IntegrationResolver
from app.services.execution.integration_registry import IntegrationRegistry, integration_registry
from app.services.execution.job_store import JobStore
from app.services.execution.queue import ExecutionQueue

logger = get_logger(__name__)


class ExecutionWorker:
    """Continuously consumes queued jobs and executes them in a daemon thread."""

    _CAPABILITY_TO_ACTION: dict[str, str] = {
        "store_data": "store_task",
        "retrieve_knowledge": "retrieve_knowledge",
        "generate_content": "generate_content",
        "schedule": "schedule_item",
        "notify": "send_notification",
    }

    def __init__(
        self,
        job_store: JobStore,
        queue: ExecutionQueue,
        resolver: IntegrationResolver | None = None,
        registry: IntegrationRegistry | None = None,
        start: bool = True,
    ) -> None:
        self.job_store = job_store
        self.queue = queue
        self.resolver = resolver or IntegrationResolver()
        self.registry = registry or integration_registry
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        if start:
            self.start()

    def start(self) -> None:
        """Start the daemon worker thread if it is not already running."""
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self.run_forever, daemon=True, name="execution-worker")
        self._thread.start()

    def stop(self) -> None:
        """Signal the worker loop to stop."""
        self._stop_event.set()

    def run_forever(self) -> None:
        """Continuously process queued jobs until stopped."""
        while not self._stop_event.is_set():
            job = self.queue.dequeue(block=True, timeout=1.0)
            if job is None:
                continue
            self._process_job(job)

    def _process_job(self, job: ExecutionJob) -> None:
        started_job = self.job_store.update(job.job_id, status=ExecutionJobStatus.running)
        logger.info("job started job_id=%s user_id=%s", started_job.job_id, started_job.user_id)

        try:
            tool_name = self._resolve_tool_name(job)
            integration = self._build_integration(tool_name)
            action = self._resolve_action(job.decision.tool_category or "")
            payload = self._build_payload(job)

            result = integration.execute(action, payload)
            self.job_store.update(job.job_id, status=ExecutionJobStatus.completed, result=result, error=None)
            logger.info("job completed job_id=%s tool_name=%s", job.job_id, tool_name)
        except Exception as exc:
            self.job_store.update(job.job_id, status=ExecutionJobStatus.failed, error=str(exc))
            logger.exception("job failed job_id=%s error=%s", job.job_id, exc)

    def _resolve_tool_name(self, job: ExecutionJob) -> str:
        capability = job.decision.tool_category or ""
        explicit_tool = job.decision.tool_name
        if explicit_tool:
            return explicit_tool

        resolved = self.resolver.resolve(capability, domain=job.decision.domain)
        if resolved:
            return resolved

        raise ValueError(f"Unsupported capability for execution: {capability}")

    def _resolve_action(self, capability: str) -> str:
        action = self._CAPABILITY_TO_ACTION.get(capability)
        if action is None:
            raise ValueError(f"Unsupported capability for execution: {capability}")
        return action

    def _build_integration(self, tool_name: str) -> Any:
        return self.registry.get_instance(tool_name)

    def _build_payload(self, job: ExecutionJob) -> dict[str, Any]:
        task_payload = job.task.model_dump(mode="json")
        decision_payload = job.decision.model_dump(mode="json")

        if job.decision.tool_category == "store_data":
            return {
                "user_id": job.user_id,
                "job_id": job.job_id,
                "task": task_payload,
                "decision": decision_payload,
            }

        if job.decision.tool_category == "retrieve_knowledge":
            query = job.task.description or job.task.title
            return {
                "user_id": job.user_id,
                "job_id": job.job_id,
                "query": query,
                "domain": job.decision.domain,
                "top_k": 5,
                "filters": {},
                "task": task_payload,
                "decision": decision_payload,
            }

        if job.decision.tool_category == "generate_content":
            return {
                "user_id": job.user_id,
                "job_id": job.job_id,
                "task": task_payload,
                "decision": decision_payload,
                "content_type": job.task.task_type,
                "instructions": job.task.description or job.task.title,
            }

        if job.decision.tool_category == "schedule":
            return {
                "user_id": job.user_id,
                "job_id": job.job_id,
                "task": task_payload,
                "decision": decision_payload,
                "schedule_window_days": 7,
            }

        if job.decision.tool_category == "notify":
            return {
                "user_id": job.user_id,
                "job_id": job.job_id,
                "task": task_payload,
                "decision": decision_payload,
                "message": job.task.description or job.task.title,
            }

        raise ValueError(f"Unsupported capability for payload building: {job.decision.tool_category}")
