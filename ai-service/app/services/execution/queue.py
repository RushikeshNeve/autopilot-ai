"""Thread-safe in-memory execution queue."""

from __future__ import annotations

from queue import Empty, Queue

from app.schemas.execution_job import ExecutionJob


class ExecutionQueue:
    """Small wrapper around Python's queue.Queue."""

    def __init__(self) -> None:
        self._queue: Queue[ExecutionJob] = Queue()

    def enqueue(self, job: ExecutionJob) -> None:
        self._queue.put(job)

    def dequeue(self, block: bool = False, timeout: float | None = None) -> ExecutionJob | None:
        try:
            if block:
                return self._queue.get(block=True, timeout=timeout)
            return self._queue.get_nowait()
        except Empty:
            return None

    def size(self) -> int:
        return self._queue.qsize()

