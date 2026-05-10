"""RAG API schemas for backend-api."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RagIngestResponse(BaseModel):
    """Response returned after document ingestion."""

    status: str = Field(default="ingested", description="Ingestion status")
    document_id: str = Field(..., description="Stable document identifier")
    filename: str = Field(..., description="Original or provided filename")
    source: str = Field(..., description="Source label for the document")
    user_id: str | None = Field(default=None, description="Optional user identifier")
    chunk_count: int = Field(..., description="Number of chunks indexed")
    chunk_ids: list[str] = Field(default_factory=list, description="Indexed chunk identifiers")


class RetrievedChunk(BaseModel):
    """Retrieved knowledge chunk returned from ai-service."""

    chunk_id: str = Field(..., description="Chunk identifier")
    document_id: str = Field(..., description="Document identifier")
    text: str = Field(..., description="Retrieved text content")
    score: float = Field(..., description="Retrieval score")
    title: str | None = Field(default=None, description="Optional chunk title")
    user_id: str | None = Field(default=None, description="Optional user identifier")
    domain: str | None = Field(default=None, description="Optional domain label")
    source: str | None = Field(default=None, description="Original content source")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = ConfigDict(from_attributes=True)


class RagQueryRequest(BaseModel):
    """Query request for grounded retrieval."""

    query: str = Field(..., min_length=1, description="Knowledge question to ask")
    user_id: str | None = Field(default=None, description="Optional user scope for retrieval")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "query": "What are the most important Node.js concepts from this guide?",
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "top_k": 5,
                }
            ]
        }
    )


class RagQueryResponse(BaseModel):
    """Grounded response returned from retrieval."""

    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated grounded answer")
    sources: list[RetrievedChunk] = Field(default_factory=list, description="Supporting source chunks")
    user_id: str | None = Field(default=None, description="Optional user scope")

