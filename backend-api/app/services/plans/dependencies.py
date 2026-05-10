"""Singleton dependencies for asynchronous planning jobs."""

from __future__ import annotations

from app.services.plans.planning_job_store import PlanningJobStore


planning_job_store = PlanningJobStore()


def get_planning_job_store() -> PlanningJobStore:
    """Return the shared planning job store."""
    return planning_job_store

