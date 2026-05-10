"""HTTP client for calling the separate ai-service."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import httpx
from fastapi import UploadFile

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class AIServiceError(RuntimeError):
    """Raised when ai-service returns an error response."""


class AIClient:
    """Reusable ai-service client used by backend-api services."""

    def __init__(self, base_url: str | None = None, timeout_seconds: float | None = None) -> None:
        settings = get_settings()
        self._base_url = base_url or settings.ai_service_url
        self._timeout = timeout_seconds or settings.http_timeout_seconds
        self._finalize_timeout = settings.ai_finalize_timeout_seconds
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout, connect=10.0, read=self._timeout, write=10.0, pool=10.0),
        )

    def interpret_goal(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Call ai-service goal interpretation."""
        return self._post_json("/ai/goals/interpret", payload)

    def finalize_plan(
        self,
        payload: dict[str, Any],
        *,
        enable_revision: bool | None = None,
        interpreted_goal: dict[str, Any] | None = None,
        progress_callback: Callable[[str, str, dict[str, Any] | None], None] | None = None,
    ) -> dict[str, Any]:
        """Finalize a plan by composing smaller ai-service calls."""
        goal_request = payload.get("goal_request")
        if not isinstance(goal_request, dict):
            raise ValueError("goal_request is required")

        user_id = str(goal_request.get("user_id") or "")
        if not user_id:
            raise ValueError("goal_request.user_id is required")

        if enable_revision is None:
            enable_revision = True

        if interpreted_goal is None:
            self._emit_progress(
                progress_callback,
                "planning_progress",
                "Interpreting goal",
                {"user_id": user_id},
            )
            interpreted_response = self.interpret_goal(goal_request)
            interpreted_goal = interpreted_response.get("interpreted_goal")
            self._emit_progress(
                progress_callback,
                "planning_progress",
                "Goal interpreted",
                {"user_id": user_id},
            )

        self._emit_progress(
            progress_callback,
            "planning_progress",
            "Generating milestones",
            {"user_id": user_id},
        )
        milestone_response = self.generate_milestones_from_interpreted(
            {
                "user_id": user_id,
                "interpreted_goal": interpreted_goal,
            }
        )
        milestones = milestone_response.get("milestones", []) or []

        all_tasks: list[dict[str, Any]] = []
        if milestones:
            self._emit_progress(
                progress_callback,
                "planning_progress",
                "Decomposing tasks",
                {"user_id": user_id, "milestones_count": len(milestones)},
            )
            tasks_by_index: dict[int, list[dict[str, Any]]] = {}
            with ThreadPoolExecutor(max_workers=min(4, len(milestones))) as executor:
                future_map = {
                    executor.submit(
                        self.generate_tasks_for_milestone,
                        {
                            "user_id": user_id,
                            "interpreted_goal": interpreted_goal,
                            "milestone": milestone,
                        },
                    ): index
                    for index, milestone in enumerate(milestones)
                }
                for future in as_completed(future_map):
                    index = future_map[future]
                    task_response = future.result()
                    tasks_by_index[index] = task_response.get("tasks", []) or []
                    milestone_id = _safe_get_milestone_id(milestones[index])
                    self._emit_progress(
                        progress_callback,
                        "planning_progress",
                        "Tasks generated",
                        {
                            "user_id": user_id,
                            "milestone_id": milestone_id,
                            "task_count": len(tasks_by_index[index]),
                        },
                    )

            for index in range(len(milestones)):
                all_tasks.extend(tasks_by_index.get(index, []))

        normalized_tasks = self._normalize_tasks(milestones, all_tasks)

        plan = self._build_final_plan(
            user_id=user_id,
            interpreted_goal=interpreted_goal,
            milestones=milestones,
            tasks=normalized_tasks,
        )
        self._emit_progress(
            progress_callback,
            "planning_progress",
            "Plan assembled",
            {"user_id": user_id, "tasks_count": len(normalized_tasks)},
        )

        critique_response = self.critique_plan({"user_id": user_id, "plan": plan})
        critique = critique_response.get("critique")

        final_plan = plan
        if enable_revision and isinstance(critique, dict) and float(critique.get("overall_score", 0.0)) < 0.85:
            self._emit_progress(
                progress_callback,
                "planning_progress",
                "Revision skipped for staged flow",
                {"user_id": user_id, "overall_score": critique.get("overall_score")},
            )

        self._emit_progress(
            progress_callback,
            "planning_progress",
            "Routing execution",
            {"user_id": user_id, "tasks_count": len(final_plan.get("tasks", []))},
        )
        execution_response = self.route_execution(
            {
                "user_id": user_id,
                "tasks": final_plan.get("tasks", []),
            }
        )

        self._emit_progress(
            progress_callback,
            "planning_progress",
            "Planning finalized",
            {"user_id": user_id},
        )
        return {
            "plan": final_plan,
            "execution": execution_response,
            "critique": critique,
        }

    def _normalize_tasks(self, milestones: list[dict[str, Any]], tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Ensure task identifiers are globally unique and dependency-safe."""
        tasks_by_milestone: dict[str, list[dict[str, Any]]] = {}
        for task in tasks:
            milestone_id = str(task.get("milestone_id") or "")
            tasks_by_milestone.setdefault(milestone_id, []).append(task)

        normalized: list[dict[str, Any]] = []
        for milestone in milestones:
            milestone_id = _safe_get_milestone_id(milestone) or "milestone"
            milestone_tasks = tasks_by_milestone.get(milestone_id, [])
            local_mapping: dict[str, str] = {}
            for index, task in enumerate(milestone_tasks, start=1):
                original_task_id = str(task.get("task_id") or f"task_{index}")
                local_mapping[original_task_id] = f"{milestone_id}_task_{index}"

            for index, task in enumerate(milestone_tasks, start=1):
                normalized_task_id = local_mapping[str(task.get("task_id") or f"task_{index}")]

                normalized_task = dict(task)
                normalized_task["task_id"] = normalized_task_id
                normalized_task["estimated_minutes"] = self._normalize_estimated_minutes(normalized_task)
                dependencies = task.get("dependencies") or []
                resolved_dependencies = [
                    local_mapping.get(str(dependency), str(dependency)) for dependency in dependencies if dependency is not None
                ]
                if not resolved_dependencies and index > 1:
                    previous_task_id = local_mapping[str(milestone_tasks[index - 2].get("task_id") or f"task_{index - 1}")]
                    resolved_dependencies.append(previous_task_id)
                normalized_task["dependencies"] = list(dict.fromkeys(resolved_dependencies))
                normalized.append(normalized_task)

        if len(normalized) != len(tasks):
            logger.warning(
                "task_normalization_count_mismatch milestones=%s original_tasks=%s normalized_tasks=%s",
                len(milestones),
                len(tasks),
                len(normalized),
            )
            return tasks

        return normalized

    def _normalize_estimated_minutes(self, task: dict[str, Any]) -> int | None:
        estimated_minutes = task.get("estimated_minutes")
        if isinstance(estimated_minutes, int) and estimated_minutes >= 5:
            return estimated_minutes

        task_type = str(task.get("task_type") or "").lower()
        priority = str(task.get("priority") or "").lower()

        base_minutes = {
            "study": 45,
            "planning": 60,
            "execution": 90,
            "review": 45,
            "drafting": 60,
        }.get(task_type, 60)

        priority_adjustment = {
            "high": 20,
            "medium": 0,
            "low": -10,
        }.get(priority, 0)

        estimate = max(15, base_minutes + priority_adjustment)
        return min(240, estimate)

    def generate_milestones_from_interpreted(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Call ai-service milestone generation for an already interpreted goal."""
        return self._post_json("/ai/planning/milestones/from-interpreted", payload)

    def generate_tasks_for_milestone(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Call ai-service task decomposition for a single milestone."""
        return self._post_json("/ai/planning/tasks", payload)

    def critique_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Call ai-service plan critique endpoint."""
        return self._post_json("/ai/evaluation/critique", payload)

    def revise_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Call ai-service plan revision endpoint."""
        return self._post_json("/ai/planning/revise", payload)

    def route_execution(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Call ai-service execution routing endpoint."""
        return self._post_json("/ai/execution/route", payload)

    def query_knowledge(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Call ai-service RAG query endpoint."""
        return self._post_json("/ai/rag/query", payload)

    def submit_execution_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Submit an execution job to ai-service."""
        return self._post_json("/ai/execution/jobs", payload)

    def get_execution_job(self, job_id: str) -> dict[str, Any]:
        """Fetch an execution job from ai-service."""
        return self._get_json(f"/ai/execution/jobs/{job_id}")

    def list_execution_jobs(self, status: str | None = None) -> list[dict[str, Any]]:
        """List execution jobs from ai-service."""
        path = "/ai/execution/jobs"
        if status is not None:
            path = f"{path}?job_status={status}"
        data = self._get_json(path)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        raise AIServiceError("Invalid execution jobs response shape")

    def approve_execution_job(self, job_id: str) -> dict[str, Any]:
        """Approve an approval-required execution job."""
        return self._post_json(f"/ai/execution/jobs/{job_id}/approve", {})

    def reject_execution_job(self, job_id: str, reason: str | None = None) -> dict[str, Any]:
        """Reject an approval-required execution job."""
        payload: dict[str, Any] = {}
        if reason is not None:
            payload["reason"] = reason
        return self._post_json(f"/ai/execution/jobs/{job_id}/reject", payload)

    def list_integrations(self) -> list[dict[str, Any]]:
        """List integration status from ai-service."""
        data = self._get_json("/ai/integrations")
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        raise AIServiceError("Invalid integrations response shape")

    def ingest_document(
        self,
        *,
        file: UploadFile | None = None,
        text: str | None = None,
        user_id: str | None = None,
        document_id: str | None = None,
        source: str = "backend_api",
        filename: str | None = None,
    ) -> dict[str, Any]:
        """Upload a document or raw text to ai-service RAG ingestion."""
        if file is None and text is None:
            raise ValueError("Either file or text must be provided")
        if file is not None and text is not None:
            raise ValueError("Provide either file or text, not both")

        data: dict[str, Any] = {"source": source}
        if user_id is not None:
            data["user_id"] = user_id
        if document_id is not None:
            data["document_id"] = document_id
        if filename is not None:
            data["filename"] = filename

        files = None
        if file is not None:
            file_bytes = file.file.read()
            upload_name = filename or file.filename or "document.bin"
            files = {
                "file": (
                    upload_name,
                    file_bytes,
                    file.content_type or "application/octet-stream",
                )
            }
        else:
            data["text"] = text or ""

        return self._post_multipart("/ai/rag/ingest", data=data, files=files)

    def _post_json(
        self,
        path: str,
        payload: dict[str, Any],
        *,
        timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """POST JSON to ai-service and normalize transport errors."""
        request_timeout = httpx.Timeout(
            timeout_seconds or self._timeout,
            connect=10.0,
            read=timeout_seconds or self._timeout,
            write=10.0,
            pool=10.0,
        )
        try:
            response = self._client.post(path, json=payload, timeout=request_timeout)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as exc:
            logger.warning("ai_service_timeout path=%s error=%s", path, exc)
            raise AIServiceError(f"ai-service request timed out for {path}") from exc
        except httpx.HTTPStatusError as exc:
            logger.warning("ai_service_http_error path=%s status=%s body=%s", path, exc.response.status_code, exc.response.text)
            raise AIServiceError(f"ai-service returned {exc.response.status_code} for {path}: {exc.response.text}") from exc
        except httpx.RequestError as exc:
            logger.warning("ai_service_connection_error path=%s error=%s", path, exc)
            raise AIServiceError(f"Failed to connect to ai-service at {path}: {exc}") from exc

    def _get_json(self, path: str) -> dict[str, Any]:
        """GET JSON from ai-service and normalize transport errors."""
        try:
            response = self._client.get(path)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as exc:
            logger.warning("ai_service_timeout path=%s error=%s", path, exc)
            raise AIServiceError(f"ai-service request timed out for {path}") from exc
        except httpx.HTTPStatusError as exc:
            logger.warning("ai_service_http_error path=%s status=%s body=%s", path, exc.response.status_code, exc.response.text)
            raise AIServiceError(f"ai-service returned {exc.response.status_code} for {path}: {exc.response.text}") from exc
        except httpx.RequestError as exc:
            logger.warning("ai_service_connection_error path=%s error=%s", path, exc)
            raise AIServiceError(f"Failed to connect to ai-service at {path}: {exc}") from exc

    def _post_multipart(
        self,
        path: str,
        *,
        data: dict[str, Any],
        files: dict[str, tuple[str, bytes, str]] | None,
    ) -> dict[str, Any]:
        """POST multipart form data to ai-service and normalize transport errors."""
        try:
            response = self._client.post(path, data=data, files=files)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as exc:
            logger.warning("ai_service_timeout path=%s error=%s", path, exc)
            raise AIServiceError(f"ai-service request timed out for {path}") from exc
        except httpx.HTTPStatusError as exc:
            logger.warning("ai_service_http_error path=%s status=%s body=%s", path, exc.response.status_code, exc.response.text)
            raise AIServiceError(f"ai-service returned {exc.response.status_code} for {path}: {exc.response.text}") from exc
        except httpx.RequestError as exc:
            logger.warning("ai_service_connection_error path=%s error=%s", path, exc)
            raise AIServiceError(f"Failed to connect to ai-service at {path}: {exc}") from exc

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def _emit_progress(
        self,
        progress_callback: Callable[[str, str, dict[str, Any] | None], None] | None,
        event_type: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        if progress_callback is not None:
            progress_callback(event_type, message, data)

    def _build_final_plan(
        self,
        *,
        user_id: str,
        interpreted_goal: dict[str, Any] | None,
        milestones: list[dict[str, Any]],
        tasks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        assumptions = self._build_assumptions(interpreted_goal)
        risks = self._build_risks(interpreted_goal)
        next_best_action = self._select_next_best_action(tasks)
        return {
            "user_id": user_id,
            "interpreted_goal": interpreted_goal,
            "milestones": milestones,
            "tasks": tasks,
            "assumptions": assumptions,
            "risks": risks,
            "next_best_action": next_best_action,
        }

    def _build_assumptions(self, interpreted_goal: dict[str, Any] | None) -> list[str]:
        assumptions: list[str] = []
        if not interpreted_goal:
            assumptions.append("Plan assumes normal execution capacity and stable availability.")
            return assumptions

        estimated_horizon = interpreted_goal.get("estimated_horizon")
        if estimated_horizon:
            assumptions.append(f"Plan assumes a working horizon of {estimated_horizon}.")

        constraints = interpreted_goal.get("constraints") or []
        if constraints:
            assumptions.append("Plan is shaped around the provided constraints.")

        if not assumptions:
            assumptions.append("Plan assumes normal execution capacity and stable availability.")
        return assumptions

    def _build_risks(self, interpreted_goal: dict[str, Any] | None) -> list[str]:
        risks: list[str] = []
        if not interpreted_goal:
            risks.append("Execution consistency is the main risk for successful completion.")
            return risks

        constraints = " ".join(str(item) for item in interpreted_goal.get("constraints") or []).lower()
        urgency = str(interpreted_goal.get("urgency") or "").lower()

        if "burnout" in constraints:
            risks.append("Overloading the schedule may reduce consistency and execution quality.")
        if urgency == "high":
            risks.append("High urgency may compress milestones and reduce execution quality.")
        if not risks:
            risks.append("Execution consistency is the main risk for successful completion.")
        return risks

    def _select_next_best_action(self, tasks: list[dict[str, Any]]) -> str:
        if not tasks:
            return "No actionable task generated yet."

        def sort_key(task: dict[str, Any]) -> tuple[int, int]:
            priority = str(task.get("priority") or "").lower()
            estimated_minutes = task.get("estimated_minutes")
            return (
                0 if priority == "high" else 1 if priority == "medium" else 2,
                int(estimated_minutes) if isinstance(estimated_minutes, int) else 9999,
            )

        sorted_tasks = sorted(tasks, key=sort_key)
        return str(sorted_tasks[0].get("title") or "No actionable task generated yet.")


def _safe_get_milestone_id(milestone: dict[str, Any]) -> str | None:
    milestone_id = milestone.get("milestone_id")
    return str(milestone_id) if milestone_id is not None else None
