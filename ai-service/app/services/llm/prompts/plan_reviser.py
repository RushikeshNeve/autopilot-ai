"""Plan reviser prompt."""
def build_plan_reviser_prompt(plan_json: str, critique_json: str) -> str:
    return f"""
You are an expert planner.

Your task is to revise an existing plan based on critique feedback.

Rules:
- Fix all high severity issues
- Improve medium issues where possible
- Keep strengths intact
- Do not degrade plan quality
- Return full updated plan
- Do not use markdown
- Return valid JSON

Input plan:
{plan_json}

Critique:
{critique_json}

Return updated plan JSON (same structure as input).
""".strip()