"""Integration status routes."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.integration import IntegrationStatus

router = APIRouter(prefix="/ai/integrations", tags=["integrations"])


@router.get("", response_model=list[IntegrationStatus], summary="List integration status")
def list_integrations() -> list[IntegrationStatus]:
    settings = get_settings()
    return [
        IntegrationStatus(
            name="RAG",
            capability="retrieve_knowledge",
            tool_name="rag_service",
            status="configured",
            description="Grounded retrieval and document ingestion for knowledge lookup.",
            configured=True,
            requires_approval=False,
            notes=["Backend and UI are connected through the RAG ingestion page."],
            details={
                "qdrant_host": settings.qdrant_host,
                "qdrant_port": settings.qdrant_port,
                "collection": settings.qdrant_collection_name,
            },
        ),
        IntegrationStatus(
            name="Notion",
            capability="store_data",
            tool_name="notion_adapter",
            status="configured" if settings.notion_api_key and settings.notion_db_id else "missing_config",
            description="Persist plans and task records into a Notion database.",
            configured=bool(settings.notion_api_key and settings.notion_db_id),
            requires_approval=False,
            notes=[
                "Used as the current storage integration for execution jobs.",
                "Requires NOTION_API_KEY and NOTION_DB_ID.",
            ],
            details={
                "notion_api_key": bool(settings.notion_api_key),
                "notion_db_id": bool(settings.notion_db_id),
            },
        ),
        IntegrationStatus(
            name="Content generation",
            capability="generate_content",
            tool_name="llm_generation_service",
            status="configured" if settings.openai_api_key else "local_fallback",
            description="Generate markdown drafts, summaries, and structured content for tasks.",
            configured=True,
            requires_approval=False,
            notes=[
                "Uses OpenAI when configured.",
                "Falls back to deterministic drafts when no API key is present.",
            ],
            details={
                "model": settings.openai_model,
                "openai_configured": bool(settings.openai_api_key),
            },
        ),
        IntegrationStatus(
            name="Scheduler",
            capability="schedule",
            tool_name="scheduler_adapter",
            status="local_fallback",
            description="Build schedule suggestions for tasks without relying on an external calendar provider.",
            configured=True,
            requires_approval=False,
            notes=["This is a local planning fallback until a calendar connector is added."],
            details={"mode": "local_schedule_suggestion"},
        ),
        IntegrationStatus(
            name="Notifications",
            capability="notify",
            tool_name="notification_adapter",
            status="local_fallback",
            description="Record notification-ready payloads in a local outbox for approval-gated work.",
            configured=True,
            requires_approval=True,
            notes=["Outbound notifications remain approval-gated and locally recorded for now."],
            details={"mode": "local_outbox"},
        ),
    ]
