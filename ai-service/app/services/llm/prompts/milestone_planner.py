"""Prompt for milestone planning."""

from app.schemas.goal import InterpretedGoal


def build_milestone_planner_prompt(
    user_id: str,
    interpreted_goal: InterpretedGoal,
    retrieved_context: str = "",
) -> str:
    return f"""
You are an expert planning system.

Your task is to break a structured user goal into 3 to 6 realistic milestones.

Rules:
- Milestones must be actionable and non-overlapping.
- Keep them logically ordered.
- Prefer practical milestones over abstract ones.
- Use realistic duration estimates for the amount of work in each milestone.
- Do not return markdown.
- Return valid JSON only.
- Use simple IDs like milestone_1, milestone_2, etc.
- priority must be one of: low, medium, high.

Input:
user_id: {user_id}

interpreted_goal:
{interpreted_goal.model_dump_json(indent=2)}

retrieved_context:
{retrieved_context if retrieved_context else "None"}

Return JSON with this exact shape:
{{
  "milestones": [
    {{
      "milestone_id": "milestone_1",
      "title": "string",
      "description": "string",
      "priority": "low|medium|high",
      "estimated_duration_days": 7
    }}
  ]
}}
""".strip()
