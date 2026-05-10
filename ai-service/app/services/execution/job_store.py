"""Thread-safe in-memory execution job store."""

from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from typing import Any

from app.schemas.execution_job import ExecutionJob


class JobNotFoundError(KeyError):
    """Raised when an execution job cannot be found."""


class DuplicateJobError(ValueError):
    """Raised when attempting to create a duplicate execution job."""


class JobStore:
    """Thread-safe file-backed job store."""

    def __init__(self) -> None:
        self._store_path = Path(__file__).resolve().parents[4] / ".data" / "execution_jobs.json"
        self._jobs: dict[str, ExecutionJob] = {}
        self._lock = RLock()
        self._load()

    def create(self, job: ExecutionJob) -> ExecutionJob:
        with self._lock:
            if job.job_id in self._jobs:
                raise DuplicateJobError(f"Execution job already exists: {job.job_id}")
            self._jobs[job.job_id] = job
            self._save_locked()
            return job

    def update(self, job_id: str, **changes: Any) -> ExecutionJob:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise JobNotFoundError(job_id)

            updated = job.model_copy(update=changes)
            self._jobs[job_id] = updated
            self._save_locked()
            return updated

    def get(self, job_id: str) -> ExecutionJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self, status: str | None = None) -> list[ExecutionJob]:
        with self._lock:
            jobs = list(self._jobs.values())
            if status is None:
                return jobs
            return [job for job in jobs if job.status == status]

    def _load(self) -> None:
        if not self._store_path.exists():
            return

        try:
            raw_jobs = json.loads(self._store_path.read_text(encoding="utf-8"))
            if not isinstance(raw_jobs, list):
                return
            for item in raw_jobs:
                if isinstance(item, dict):
                    job = ExecutionJob.model_validate(item)
                    self._jobs[job.job_id] = job
        except Exception:
            self._jobs = {}

    def _save_locked(self) -> None:
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [job.model_dump(mode="json") for job in self._jobs.values()]
        tmp_path = self._store_path.with_suffix(self._store_path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp_path.replace(self._store_path)


# Backward-compatible alias for the earlier scaffold.
ExecutionJobStore = JobStore
