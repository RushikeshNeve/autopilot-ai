"""Indexing helpers for the reusable RAG ingestion pipeline."""

from __future__ import annotations

from typing import Any
from uuid import NAMESPACE_URL, uuid4, uuid5

from app.core.logger import get_logger
from app.db.qdrant import QdrantDB, QdrantDBError
from app.rag.ingestion.chunker import Chunker
from app.rag.ingestion.embedder import Embedder
from app.rag.schemas import DocumentChunk

logger = get_logger(__name__)


class Indexer:
    """Prepare embedded chunks for future vector database storage."""

    def __init__(
        self,
        embedder: Embedder | None = None,
        chunker: Chunker | None = None,
        qdrant_db: QdrantDB | None = None,
    ) -> None:
        self._embedder = embedder or Embedder()
        self._chunker = chunker or Chunker()
        self._qdrant_db = qdrant_db or QdrantDB()

    def index_document(
        self,
        document_id: str,
        source: str,
        text: str,
        user_id: str | None = None,
    ) -> list[DocumentChunk]:
        """Chunk and embed a document, returning storage-ready chunk records.

        The return value is intentionally storage-agnostic so it can later be
        handed to Qdrant or another vector store with minimal conversion.
        """
        chunks = self._chunker.chunk_text(text)
        if not chunks:
            return []

        embeddings = self._embedder.embed_texts(chunks)
        prepared: list[DocumentChunk] = []

        for index, (chunk_text, embedding) in enumerate(zip(chunks, embeddings, strict=True), start=1):
            chunk_id = f"{document_id}_chunk_{index}_{uuid4().hex[:8]}"
            prepared.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    content=chunk_text,
                    title=None,
                    user_id=user_id,
                    domain=None,
                    source=source,
                    metadata={
                        "chunk_index": index,
                        "embedding_model": self._embedder.model,
                        "embedding_dimensions": len(embedding),
                        "embedding": embedding,
                        "storage_target": "qdrant",
                        "indexed": False,
                    },
                )
            )

        logger.info(
            "rag_index_document_prepared document_id=%s source=%s chunks=%s user_id=%s",
            document_id,
            source,
            len(prepared),
            user_id,
        )

        try:
            self._qdrant_db.ensure_collection(vector_size=len(embeddings[0]))
            self._qdrant_db.upsert_chunks([self.to_qdrant_payload(chunk) for chunk in prepared])
        except QdrantDBError:
            raise
        except Exception as exc:
            logger.exception("rag_index_document_failed document_id=%s source=%s", document_id, source)
            raise RuntimeError(f"Failed to index document '{document_id}': {exc}") from exc

        return prepared

    def to_qdrant_payload(self, chunk: DocumentChunk) -> dict[str, Any]:
        """Convert a prepared chunk into a future Qdrant point payload."""
        return {
            "id": str(uuid5(NAMESPACE_URL, chunk.chunk_id)),
            "vector": chunk.metadata.get("embedding", []),
            "payload": {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "content": chunk.content,
                "source": chunk.source,
                "user_id": chunk.user_id,
                "domain": chunk.domain,
                "title": chunk.title,
                "metadata": chunk.metadata,
            },
        }
