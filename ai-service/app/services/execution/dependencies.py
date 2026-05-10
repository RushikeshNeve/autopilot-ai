"""Singleton dependencies for the execution system."""

from __future__ import annotations

from app.services.execution.execution_service import ExecutionService
from app.services.execution.integration_registry import IntegrationRegistry, integration_registry
from app.services.execution.job_store import JobStore
from app.services.execution.queue import ExecutionQueue
from app.services.execution.worker import ExecutionWorker


job_store = JobStore()
execution_queue = ExecutionQueue()
integration_registry_singleton: IntegrationRegistry = integration_registry
execution_service = ExecutionService(job_store=job_store, queue=execution_queue)
execution_worker = ExecutionWorker(
    job_store=job_store,
    queue=execution_queue,
    registry=integration_registry_singleton,
    start=False,
)


def get_job_store() -> JobStore:
    return job_store


def get_execution_queue() -> ExecutionQueue:
    return execution_queue


def get_integration_registry() -> IntegrationRegistry:
    return integration_registry_singleton


def get_execution_service() -> ExecutionService:
    return execution_service


def get_execution_worker() -> ExecutionWorker:
    return execution_worker

