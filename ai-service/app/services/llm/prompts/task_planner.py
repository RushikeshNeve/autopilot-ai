"""Prompt for task planning."""

from app.schemas.goal import InterpretedGoal
from app.schemas.task import Milestone


def build_task_planner_prompt(
    user_id: str,
    interpreted_goal: InterpretedGoal,
    milestone: Milestone,
    retrieved_context: str = "",
) -> str:
    return f"""
You are an expert execution planner.

Your task is to generate 4 to 8 concrete tasks for one milestone.

Rules:
- Tasks must be specific and practical.
- Avoid vague tasks like "work harder" or "prepare more".
- Keep tasks aligned to the milestone and interpreted goal.
- Use realistic estimates based on the actual work involved.
- Respect dependencies when relevant, but only add a dependency when one task truly needs another first.
- Do not return markdown.
- Return valid JSON only.
 - Use globally unique IDs like "{milestone.milestone_id}_task_1", "{milestone.milestone_id}_task_2", etc.
- task_type should be something like planning, study, execution, review, drafting.
- priority must be one of: low, medium, high.

Input:
user_id: {user_id}

interpreted_goal:
{interpreted_goal.model_dump_json(indent=2)}

milestone:
{milestone.model_dump_json(indent=2)}

retrieved_context:
{retrieved_context if retrieved_context else "None"}

Return JSON with this exact shape:
{{
  "tasks": [
    {{
      "task_id": "{milestone.milestone_id}_task_1",
      "milestone_id": "{milestone.milestone_id}",
      "title": "string",
      "description": "string",
      "task_type": "string",
      "priority": "low|medium|high",
      "estimated_minutes": 60,
      "dependencies": ["{milestone.milestone_id}_task_1"],
      "requires_approval": false,
      "suggested_tools": ["string"]
    }}
  ]
}}
""".strip()
