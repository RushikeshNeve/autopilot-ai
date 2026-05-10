"""Embedding utilities for the reusable RAG layer."""

from __future__ import annotations

from typing import Any

from openai import OpenAI

from app.core.config import get_settings


class Embedder:
    """OpenAI-backed text embedder."""

    def __init__(self, model: str | None = None, client: OpenAI | None = None) -> None:
        settings = get_settings()
        self.model = model or "text-embedding-3-small"
        self._client = client or OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout,
            max_retries=settings.openai_max_retries,
        )

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text string."""
        response = self._client.embeddings.create(model=self.model, input=text)
        return list(response.data[0].embedding)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple text strings."""
        response = self._client.embeddings.create(model=self.model, input=texts)
        return [list(item.embedding) for item in response.data]

