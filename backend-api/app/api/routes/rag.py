"""RAG orchestration routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.schemas.rag import RagIngestResponse, RagQueryRequest, RagQueryResponse
from app.services.ai.ai_client import AIClient, AIServiceError

router = APIRouter(prefix="/ai/rag", tags=["rag"])

ai_client = AIClient()


@router.post(
    "/ingest",
    response_model=RagIngestResponse,
    summary="Ingest document into RAG",
    description="Proxy document or raw-text ingestion through ai-service and return the ingestion result.",
)
def ingest_document(
    file: UploadFile | None = File(default=None, description="PDF, markdown, or text file upload"),
    text: str | None = Form(default=None, description="Raw text to ingest when no file is provided"),
    user_id: str | None = Form(default=None, description="Optional user scope for ingestion"),
    document_id: str | None = Form(default=None, description="Optional stable document identifier"),
    source: str = Form(default="backend_api", description="Source label for the ingested content"),
    filename: str | None = Form(default=None, description="Optional filename override"),
) -> RagIngestResponse:
    try:
        result = ai_client.ingest_document(
            file=file,
            text=text,
            user_id=user_id,
            document_id=document_id,
            source=source,
            filename=filename,
        )
        return RagIngestResponse.model_validate(result)
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post(
    "/query",
    response_model=RagQueryResponse,
    summary="Query RAG knowledge",
    description="Proxy a grounded retrieval query through ai-service and return the answer plus sources.",
)
def query_knowledge(payload: RagQueryRequest) -> RagQueryResponse:
    try:
        result = ai_client.query_knowledge(payload.model_dump())
        return RagQueryResponse.model_validate(result)
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

