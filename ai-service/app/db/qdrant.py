"""Qdrant connection helpers."""

from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient, models

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class QdrantDBError(RuntimeError):
    """Raised when Qdrant operations fail."""


class QdrantDB:
    """Small wrapper around Qdrant client operations.

    This class keeps business logic out of the database adapter and exposes a
    narrow API for ingestion and retrieval.
    """

    def __init__(
        self,
        client: QdrantClient | None = None,
        collection_name: str | None = None,
    ) -> None:
        settings = get_settings()
        self.collection_name = collection_name or settings.qdrant_collection_name
        self._client = client or QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )

    def ensure_collection(self, vector_size: int) -> None:
        """Create the collection if it does not already exist."""
        try:
            if self._client.collection_exists(self.collection_name):
                return

            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE,
                ),
            )
            logger.info(
                "qdrant_collection_created collection_name=%s vector_size=%s",
                self.collection_name,
                vector_size,
            )
        except Exception as exc:
            logger.exception("qdrant_ensure_collection_failed collection_name=%s", self.collection_name)
            raise QdrantDBError(f"Failed to ensure Qdrant collection '{self.collection_name}': {exc}") from exc

    def upsert_chunks(self, chunks: list[dict[str, Any]]) -> None:
        """Upsert prepared chunks into Qdrant."""
        if not chunks:
            return

        try:
            points = []
            for chunk in chunks:
                point_id = chunk.get("id") or chunk.get("chunk_id")
                vector = chunk.get("vector")
                payload = chunk.get("payload") or {}
                if point_id is None:
                    raise ValueError("Qdrant chunk is missing an id")
                if vector is None:
                    raise ValueError(f"Qdrant chunk '{point_id}' is missing a vector")

                points.append(
                    models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload,
                    )
                )

            self._client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True,
            )
            logger.info("qdrant_upsert_completed collection_name=%s points=%s", self.collection_name, len(points))
        except Exception as exc:
            logger.exception("qdrant_upsert_failed collection_name=%s", self.collection_name)
            raise QdrantDBError(f"Failed to upsert chunks into '{self.collection_name}': {exc}") from exc

    def search(
        self,
        query_vector: list[float],
        user_id: str | None = None,
        top_k: int = 5,
        metadata_filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for nearest chunks in Qdrant."""
        try:
            query_filter = self._build_filter(user_id=user_id, metadata_filters=metadata_filters)
            if hasattr(self._client, "query_points"):
                result = self._client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=query_filter,
                    limit=top_k,
                    with_payload=True,
                    with_vectors=False,
                )
                hits = getattr(result, "points", result)
            else:
                hits = self._client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=top_k,
                    with_payload=True,
                    with_vectors=False,
                )
            return [
                {
                    "id": str(hit.id),
                    "score": float(hit.score or 0.0),
                    "payload": dict(hit.payload or {}),
                }
                for hit in hits
            ]
        except Exception as exc:
            logger.exception("qdrant_search_failed collection_name=%s", self.collection_name)
            raise QdrantDBError(f"Failed to search Qdrant collection '{self.collection_name}': {exc}") from exc

    def _build_filter(
        self,
        user_id: str | None = None,
        metadata_filters: dict[str, Any] | None = None,
    ) -> models.Filter | None:
        conditions: list[models.FieldCondition] = []

        if user_id is not None:
            conditions.append(
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=user_id),
                )
            )

        if metadata_filters:
            for key, value in metadata_filters.items():
                if value is None:
                    continue
                if isinstance(value, (list, tuple, set)):
                    conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchAny(any=list(value)),
                        )
                    )
                else:
                    conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value),
                        )
                    )

        if not conditions:
            return None

        return models.Filter(must=conditions)
