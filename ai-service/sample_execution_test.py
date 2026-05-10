"""Simple execution system smoke test.

Run with:
  python sample_execution_test.py --base-url http://127.0.0.1:8001

This submits four example jobs and polls each job until it reaches a terminal state.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from dataclasses import dataclass
from typing import Any

import requests


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("sample_execution_test")


@dataclass(frozen=True)
class ExecutionCase:
    name: str
    payload: dict[str, Any]


def build_cases() -> list[ExecutionCase]:
    base_task = {
        "milestone_id": "ms_001",
        "priority": "high",
        "estimated_minutes": 30,
        "dependencies": [],
        "requires_approval": False,
        "suggested_tools": [],
    }

    return [
        ExecutionCase(
            name="auto_execute_rag",
            payload={
                "user_id": "user_demo_1",
                "task": {
                    **base_task,
                    "task_id": "task_rag_001",
                    "title": "Research Python queue patterns",
                    "description": "Find grounded information on using queue.Queue for worker pipelines.",
                    "task_type": "study",
                },
                "decision": {
                    "task_id": "task_rag_001",
                    "action_mode": "auto_execute",
                    "tool_category": "retrieve_knowledge",
                    "tool_name": "rag",
                    "domain": "engineering",
                    "reason": "Safe to retrieve knowledge automatically",
                    "confidence": 0.94,
                },
            },
        ),
        ExecutionCase(
            name="auto_execute_notion",
            payload={
                "user_id": "user_demo_1",
                "task": {
                    **base_task,
                    "task_id": "task_notion_001",
                    "title": "Store meeting notes",
                    "description": "Save the meeting summary to Notion for later reference.",
                    "task_type": "execution",
                },
                "decision": {
                    "task_id": "task_notion_001",
                    "action_mode": "auto_execute",
                    "tool_category": "store_data",
                    "tool_name": "notion",
                    "domain": "operations",
                    "reason": "Safe to store task data automatically",
                    "confidence": 0.92,
                },
            },
        ),
        ExecutionCase(
            name="manual_task",
            payload={
                "user_id": "user_demo_1",
                "task": {
                    **base_task,
                    "task_id": "task_manual_001",
                    "title": "Review project plan",
                    "description": "User should review and approve the project plan manually.",
                    "task_type": "review",
                },
                "decision": {
                    "task_id": "task_manual_001",
                    "action_mode": "manual",
                    "tool_category": "generate_content",
                    "tool_name": None,
                    "domain": "planning",
                    "reason": "User review is required",
                    "confidence": 0.81,
                },
            },
        ),
        ExecutionCase(
            name="requires_approval_task",
            payload={
                "user_id": "user_demo_1",
                "task": {
                    **base_task,
                    "task_id": "task_approval_001",
                    "title": "Send external email",
                    "description": "This task requires explicit approval before sending.",
                    "task_type": "execution",
                    "requires_approval": True,
                },
                "decision": {
                    "task_id": "task_approval_001",
                    "action_mode": "requires_approval",
                    "tool_category": "notify",
                    "tool_name": None,
                    "domain": "communication",
                    "reason": "Approval is required before outbound communication",
                    "confidence": 0.99,
                },
            },
        ),
    ]


def submit_job(base_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/ai/execution/jobs"
    logger.info("Submitting job to %s", url)
    response = requests.post(url, json=payload, timeout=30)
    logger.info("Submit response status=%s body=%s", response.status_code, response.text)
    response.raise_for_status()
    return response.json()


def poll_job(base_url: str, job_id: str, timeout_seconds: int = 60, interval_seconds: float = 2.0) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/ai/execution/jobs/{job_id}"
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        response = requests.get(url, timeout=30)
        logger.info("Poll job_id=%s status_code=%s body=%s", job_id, response.status_code, response.text)
        response.raise_for_status()
        data = response.json()
        if data.get("status") in {"completed", "failed", "requires_approval"}:
            return data
        time.sleep(interval_seconds)

    raise TimeoutError(f"Job {job_id} did not reach a terminal state within {timeout_seconds}s")


def run_case(base_url: str, case: ExecutionCase) -> None:
    logger.info("=== Running case: %s ===", case.name)
    submit_result = submit_job(base_url, case.payload)
    job_id = submit_result["job_id"]
    logger.info("Submitted case=%s job_id=%s initial_status=%s", case.name, job_id, submit_result["status"])

    final_result = poll_job(base_url, job_id)
    logger.info(
        "Final case=%s job_id=%s status=%s result=%s error=%s",
        case.name,
        job_id,
        final_result.get("status"),
        final_result.get("result"),
        final_result.get("error"),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execution system smoke test")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8001",
        help="Base URL for the FastAPI service",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logger.info("Starting execution smoke test against %s", args.base_url)

    for case in build_cases():
        try:
            run_case(args.base_url, case)
        except Exception as exc:
            logger.exception("Case failed: %s", case.name)
            print(f"[FAIL] {case.name}: {exc}", file=sys.stderr)

    logger.info("Execution smoke test complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

