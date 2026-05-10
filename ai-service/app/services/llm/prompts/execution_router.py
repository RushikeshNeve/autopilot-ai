"""Prompt for execution routing."""
from app.services.execution.capability_registry import CORE_CAPABILITIES


def build_execution_router_prompt(user_id: str, tasks_json: str) -> str:
    capabilities_text = "\n".join(
        f"- {name}: {meta['description']}"
        for name, meta in CORE_CAPABILITIES.items()
    )

    return f"""
You are an AI execution router.

Your task is to decide how each task should be handled.

Available action modes:
- suggest: recommend it to the user only
- auto_execute: safe for the system to execute automatically
- requires_approval: requires explicit user confirmation
- manual: the user must perform it themselves

Available capabilities:
{capabilities_text}

Rules:
- Be conservative with auto_execute
- Use retrieve_knowledge for concept explanations, grounded retrieval, or reference lookup
- Use generate_content for notes, summaries, drafts, and generated outputs
- Use store_data for saving tasks, notes, or outputs
- Use schedule for reminders, study slots, or structured scheduling
- Use notify for outbound communication
- Anything externally risky or user-sensitive should require approval
- Return valid JSON only
- Do not return markdown

Input:
user_id: {user_id}

tasks:
{tasks_json}

Return JSON:
{{
  "decisions": [
    {{
      "task_id": "task_1",
      "action_mode": "auto_execute",
      "tool_category": "generate_content",
      "tool_name": null,
      "domain": "study",
      "reason": "Safe to generate structured study notes automatically",
      "confidence": 0.91
    }}
  ]
}}
""".strip()