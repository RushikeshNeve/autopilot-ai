"""Text chunking helpers for the reusable RAG ingestion pipeline."""

from __future__ import annotations


class Chunker:
    """Deterministically split text into overlapping chunks."""

    def chunk_text(self, text: str, chunk_size: int = 800, chunk_overlap: int = 150) -> list[str]:
        """Split text into chunks using a simple character window strategy.

        The implementation prefers paragraph boundaries when possible and falls
        back to fixed-width slicing for long segments.
        """
        normalized = self._normalize_text(text)
        if not normalized:
            return []

        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        paragraphs = [part.strip() for part in normalized.split("\n\n") if part.strip()]
        chunks: list[str] = []
        current = ""

        for paragraph in paragraphs:
            if not current:
                current = paragraph
                continue

            candidate = f"{current}\n\n{paragraph}"
            if len(candidate) <= chunk_size:
                current = candidate
                continue

            chunks.extend(self._slice_long_text(current, chunk_size=chunk_size, chunk_overlap=chunk_overlap))
            current = paragraph

        if current:
            chunks.extend(self._slice_long_text(current, chunk_size=chunk_size, chunk_overlap=chunk_overlap))

        return [chunk for chunk in chunks if chunk.strip()]

    def _normalize_text(self, text: str) -> str:
        return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")).strip()

    def _slice_long_text(self, text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
        if len(text) <= chunk_size:
            return [text.strip()] if text.strip() else []

        chunks: list[str] = []
        start = 0
        step = chunk_size - chunk_overlap

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(text):
                break
            start += step

        return chunks

