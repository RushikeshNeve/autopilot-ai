"""Thread-safe in-memory store for asynchronous plan jobs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlanningJobRecord(BaseModel):
    """Internal representation of a queued plan finalization job."""

    job_id: str = Field(..., description="Planning job identifier")
    goal_id: UUID = Field(..., description="Related goal identifier")
    workspace_id: UUID = Field(..., description="Related workspace identifier")
    user_id: UUID = Field(..., description="Owning user identifier")
    status: str = Field(default="queued", description="Current job status")
    request_payload: dict[str, object] = Field(default_factory=dict, description="Original job request payload")
    result: dict[str, object] | None = Field(default=None, description="Serialized plan result")
    error: str | None = Field(default=None, description="Failure message if the job failed")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


class PlanningJobStore:
    """Thread-safe file-backed job store for plan finalization jobs."""

    def __init__(self) -> None:
        self._store_path = Path(__file__).resolve().parents[4] / ".data" / "planning_jobs.json"
        self._jobs: dict[str, PlanningJobRecord] = {}
        self._lock = RLock()
        self._load()

    def create(
        self,
        *,
        job_id: str,
        goal_id: UUID,
        workspace_id: UUID,
        user_id: UUID,
        request_payload: dict[str, object],
    ) -> PlanningJobRecord:
        """Create a new planning job record."""
        job = PlanningJobRecord(
            job_id=job_id,
            goal_id=goal_id,
            workspace_id=workspace_id,
            user_id=user_id,
            request_payload=request_payload,
        )
        with self._lock:
            self._jobs[job_id] = job
            self._save_locked()
        return job

    def update(
        self,
        job_id: str,
        *,
        status: str | None = None,
        result: dict[str, object] | None = None,
        error: str | None = None,
    ) -> PlanningJobRecord:
        """Update a planning job and return the new record."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise KeyError(job_id)

            if status is not None:
                job.status = status
            if result is not None or status == "completed":
                job.result = result
            if error is not None:
                job.error = error
            job.updated_at = datetime.now(timezone.utc)
            self._jobs[job_id] = job
            self._save_locked()
            return job

    def get(self, job_id: str) -> PlanningJobRecord | None:
        """Fetch a planning job by identifier."""
        with self._lock:
            return self._jobs.get(job_id)

    def list(self) -> list[PlanningJobRecord]:
        """Return all planning jobs."""
        with self._lock:
            return list(self._jobs.values())

    def _load(self) -> None:
        if not self._store_path.exists():
            return

        try:
            raw_jobs = json.loads(self._store_path.read_text(encoding="utf-8"))
            if not isinstance(raw_jobs, list):
                return
            for item in raw_jobs:
                if isinstance(item, dict):
                    job = PlanningJobRecord.model_validate(item)
                    self._jobs[job.job_id] = job
        except Exception:
            self._jobs = {}

    def _save_locked(self) -> None:
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [job.model_dump(mode="json") for job in self._jobs.values()]
        tmp_path = self._store_path.with_suffix(self._store_path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp_path.replace(self._store_path)
