"""Prompt for goal interpretation."""

from app.schemas.goal import GoalInterpretRequest


def build_goal_interpreter_prompt(request: GoalInterpretRequest, retrieved_context: str = "") -> str:
    constraints_text = (
        "\n".join(f"- {constraint}" for constraint in request.constraints)
        if request.constraints
        else "- None provided"
    )

    domain_hint_text = request.domain_hint if request.domain_hint else "None"

    return f"""
You are an expert AI planning analyst.

Your task is to interpret a user's raw goal into a structured JSON object.

Rules:
- Be precise and realistic.
- Infer implied constraints only when strongly supported.
- Keep the reasoning_summary short and safe.
- Do not return markdown.
- Return valid JSON only.
- Use simple snake_case strings for categorical fields where possible.
- confidence must be between 0 and 1.

Input:
user_id: {request.user_id}
domain_hint: {domain_hint_text}
goal_text: {request.goal_text}

explicit_constraints:
{constraints_text}

retrieved_context:
{retrieved_context if retrieved_context else "None"}

Return JSON with this exact shape:
{{
  "primary_intent": "string",
  "sub_intents": ["string"],
  "domain": "string",
  "target_outcomes": ["string"],
  "constraints": ["string"],
  "estimated_horizon": "string",
  "urgency": "low|medium|high",
  "confidence": 0.0,
  "reasoning_summary": "string"
}}
""".strip()
