"""Approval policy logic."""

from app.schemas.execution import ExecutionDecision


APPROVAL_KEYWORDS = [
    "send",
    "email",
    "submit",
    "delete",
    "apply",
    "purchase",
    "payment",
    "share",
]


def enforce_approval_policy(decision: ExecutionDecision) -> ExecutionDecision:
    text = f"{decision.reason} {decision.tool_category or ''} {decision.tool_name or ''}".lower()

    if any(keyword in text for keyword in APPROVAL_KEYWORDS):
        decision.action_mode = "requires_approval"

    if decision.tool_category == "notify":
        decision.action_mode = "requires_approval"

    return decision