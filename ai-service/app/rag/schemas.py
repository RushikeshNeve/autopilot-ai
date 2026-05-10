"""Shared schemas for the reusable RAG layer."""

from __future__ import annotations

from typing import Any
from typing import Literal

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """A chunk of source content that can be embedded and retrieved."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Unique source document identifier")
    content: str = Field(..., description="Chunk text content")
    title: str | None = Field(default=None, description="Optional source title")
    user_id: str | None = Field(default=None, description="Optional owner/user scope")
    domain: str | None = Field(default=None, description="Optional domain scope")
    source: str | None = Field(default=None, description="Human readable source label")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional source metadata")

    @property
    def text(self) -> str:
        """Backward-compatible alias for older callers."""
        return self.content


class RetrievedChunk(BaseModel):
    """A ranked retrieval result returned by the retriever."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Unique source document identifier")
    text: str = Field(..., description="Chunk text content")
    score: float = Field(..., description="Similarity or relevance score")
    title: str | None = Field(default=None, description="Optional source title")
    user_id: str | None = Field(default=None, description="Optional owner/user scope")
    domain: str | None = Field(default=None, description="Optional domain scope")
    source: str | None = Field(default=None, description="Human readable source label")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional source metadata")


class RAGQueryRequest(BaseModel):
    """Input payload for a RAG query."""

    query: str = Field(..., min_length=1, description="Natural language question or prompt")
    user_id: str | None = Field(default=None, description="Optional user scope for retrieval")
    domain: str | None = Field(default=None, description="Optional domain scope")
    top_k: int = Field(default=5, ge=1, le=20, description="Maximum number of chunks to retrieve")
    filters: dict[str, Any] = Field(default_factory=dict, description="Additional retrieval filters")


class RAGQueryResponse(BaseModel):
    """Answer payload returned by the RAG service."""

    query: str = Field(..., description="Original user query")
    answer: str = Field(..., description="Generated grounded answer")
    sources: list[RetrievedChunk] = Field(default_factory=list, description="Retrieved supporting chunks")


class RAGIngestResponse(BaseModel):
    """Response payload returned after ingesting a document into RAG."""

    status: Literal["ingested"] = Field(default="ingested", description="Ingestion outcome")
    document_id: str = Field(..., description="Canonical document identifier")
    filename: str = Field(..., description="Original uploaded file name")
    source: str = Field(..., description="Human readable source label")
    user_id: str | None = Field(default=None, description="Optional owner/user scope")
    chunk_count: int = Field(..., ge=0, description="Number of indexed chunks")
    chunk_ids: list[str] = Field(default_factory=list, description="Indexed chunk identifiers")
