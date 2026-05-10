"""RAG integration adapter."""

from __future__ import annotations

from typing import Any

from app.rag.schemas import RAGQueryRequest
from app.rag.service import RAGService
from app.services.execution.integration_base import BaseIntegration


class RAGAdapter(BaseIntegration):
    """Bridge execution requests to the reusable RAG service."""

    name = "rag_service"
    action = "retrieve_knowledge"

    def __init__(self, rag_service: RAGService | None = None) -> None:
        self._rag_service = rag_service or RAGService()

    def execute(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        if action != self.action:
            raise ValueError(f"Unsupported action for RAGAdapter: {action}")

        query = payload.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("RAG payload requires a non-empty query")

        request = RAGQueryRequest(
            query=query,
            user_id=payload.get("user_id"),
            domain=payload.get("domain"),
            top_k=int(payload.get("top_k", 5)),
            filters=dict(payload.get("filters") or {}),
        )

        response = self._rag_service.query(request)
        return {
            "integration": self.name,
            "action": action,
            "query": response.query,
            "answer": response.answer,
            "sources": [source.model_dump(mode="json") for source in response.sources],
        }


RagAdapter = RAGAdapter
