"""Retrieval utilities for the reusable RAG layer."""

from __future__ import annotations

from app.core.logger import get_logger
from app.db.qdrant import QdrantDB, QdrantDBError
from app.rag.ingestion.embedder import Embedder
from app.rag.schemas import RetrievedChunk

logger = get_logger(__name__)


class Retriever:
    """Retrieves relevant chunks from Qdrant."""

    def __init__(self, embedder: Embedder | None = None, qdrant_db: QdrantDB | None = None) -> None:
        self._embedder = embedder or Embedder()
        self._qdrant_db = qdrant_db or QdrantDB()

    def retrieve(
        self,
        query: str,
        user_id: str | None = None,
        top_k: int = 5,
        filters: dict[str, object] | None = None,
    ) -> list[RetrievedChunk]:
        """Embed the query and return the top relevant chunks."""
        logger.info(
            "rag_retrieve_started query_chars=%s user_id=%s top_k=%s",
            len(query),
            user_id,
            top_k,
        )

        try:
            query_vector = self._embedder.embed_text(query)
            results = self._qdrant_db.search(
                query_vector=query_vector,
                user_id=user_id,
                top_k=top_k,
                metadata_filters=filters,
            )
            return [self._map_result(item) for item in results]
        except QdrantDBError:
            raise
        except Exception as exc:
            logger.exception("rag_retrieve_failed user_id=%s", user_id)
            raise RuntimeError(f"RAG retrieval failed: {exc}") from exc

    def _map_result(self, result: dict[str, object]) -> RetrievedChunk:
        payload = dict(result.get("payload") or {})
        return RetrievedChunk(
            chunk_id=str(payload.get("chunk_id") or result.get("id") or ""),
            document_id=str(payload.get("document_id") or result.get("id") or ""),
            text=str(payload.get("content") or payload.get("text") or ""),
            score=float(result.get("score") or 0.0),
            title=payload.get("title"),
            user_id=payload.get("user_id"),
            domain=payload.get("domain"),
            source=payload.get("source"),
            metadata=dict(payload.get("metadata") or {}),
        )
