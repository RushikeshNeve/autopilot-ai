"""Helpers for formatting and retrieving RAG context for prompts."""

from __future__ import annotations

from app.core.logger import get_logger
from app.rag.schemas import RetrievedChunk
from app.rag.service import RAGService

logger = get_logger(__name__)


def format_retrieved_context(
    chunks: list[RetrievedChunk],
    max_chunks: int = 4,
    max_chars: int = 1200,
) -> str:
    """Render retrieved chunks into a compact, prompt-friendly text block."""
    if not chunks:
        return ""

    lines: list[str] = []
    total_chars = 0

    for index, chunk in enumerate(chunks[:max_chunks], start=1):
        block = (
            f"[Context {index}] "
            f"source={chunk.source or 'unknown'} "
            f"document_id={chunk.document_id} "
            f"chunk_id={chunk.chunk_id} "
            f"score={chunk.score:.3f}\n"
            f"{chunk.text.strip()}"
        )
        if total_chars + len(block) > max_chars and lines:
            break
        lines.append(block)
        total_chars += len(block)

    return "\n\n".join(lines).strip()


def get_retrieved_context_text(
    rag_service: RAGService,
    query: str,
    user_id: str | None = None,
    domain: str | None = None,
    top_k: int = 3,
    max_chunks: int = 4,
    max_chars: int = 1200,
    filters: dict[str, object] | None = None,
) -> str:
    """Query RAG and render a compact prompt-safe context block.

    This helper keeps planner and critique services free of retrieval boilerplate
    while preserving a safe fallback if retrieval is unavailable.
    """
    try:
        chunks = rag_service.retrieve_chunks(
            query=query,
            user_id=user_id,
            top_k=top_k,
            filters=filters or {},
        )
    except Exception as exc:
        logger.warning("rag_context_unavailable user_id=%s error=%s", user_id, exc)
        return ""

    return format_retrieved_context(chunks, max_chunks=max_chunks, max_chars=max_chars)
