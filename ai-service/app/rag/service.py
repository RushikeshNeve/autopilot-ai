"""Reusable RAG service."""

from __future__ import annotations

from app.rag.generation.answer_generator import AnswerGenerator
from app.rag.retrieval.retriever import Retriever
from app.rag.schemas import RAGQueryRequest, RAGQueryResponse


class RAGService:
    """High-level retrieval-augmented generation service."""

    def __init__(
        self,
        retriever: Retriever | None = None,
        answer_generator: AnswerGenerator | None = None,
    ) -> None:
        self._retriever = retriever or Retriever()
        self._answer_generator = answer_generator or AnswerGenerator()

    def query(self, request: RAGQueryRequest) -> RAGQueryResponse:
        """Run retrieve -> generate and return the final response."""
        chunks = self._retriever.retrieve(
            query=request.query,
            user_id=request.user_id,
            top_k=request.top_k,
            filters=request.filters,
        )
        answer = self._answer_generator.generate(query=request.query, retrieved_chunks=chunks)
        return RAGQueryResponse(
            query=request.query,
            answer=answer,
            sources=chunks,
        )

    def retrieve_chunks(
        self,
        query: str,
        user_id: str | None = None,
        top_k: int = 5,
        filters: dict[str, object] | None = None,
    ) -> list:
        """Return retrieved chunks without spending tokens on answer generation."""
        return self._retriever.retrieve(
            query=query,
            user_id=user_id,
            top_k=top_k,
            filters=filters,
        )
