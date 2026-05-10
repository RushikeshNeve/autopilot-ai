"""Answer generation utilities for the reusable RAG layer."""

from __future__ import annotations

from app.core.logger import get_logger
from app.rag.schemas import RetrievedChunk
from app.services.llm.client import LLMClient

logger = get_logger(__name__)


class AnswerGenerator:
    """Builds a grounded prompt and generates a final answer."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm_client = llm_client or LLMClient()

    def generate(self, query: str, retrieved_chunks: list[RetrievedChunk]) -> str:
        """Generate a grounded answer from the retrieved context."""
        prompt = self._build_prompt(query=query, retrieved_chunks=retrieved_chunks)
        logger.info(
            "rag_generate_started query_chars=%s chunks=%s",
            len(query),
            len(retrieved_chunks),
        )
        return self._llm_client.generate_text(prompt)

    def _build_prompt(self, query: str, retrieved_chunks: list[RetrievedChunk]) -> str:
        context_lines: list[str] = []
        for index, chunk in enumerate(retrieved_chunks, start=1):
            context_lines.append(
                f"[Source {index}] "
                f"chunk_id={chunk.chunk_id} "
                f"document_id={chunk.document_id} "
                f"score={chunk.score:.3f} "
                f"title={chunk.title or 'N/A'}\n"
                f"{chunk.text}"
            )

        context_block = "\n\n".join(context_lines) if context_lines else "No supporting context was retrieved."

        return (
            "You are a grounded assistant answering with the provided context only when possible.\n"
            "If the context is insufficient, say what is missing rather than inventing facts.\n\n"
            f"User query:\n{query}\n\n"
            f"Retrieved context:\n{context_block}\n\n"
            "Write a clear, concise answer that is useful across domains."
        )

