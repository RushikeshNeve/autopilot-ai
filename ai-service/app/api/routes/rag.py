"""RAG API routes for ingestion and retrieval."""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.rag.ingestion.ingestion_service import RAGIngestionService
from app.rag.schemas import RAGIngestResponse

router = APIRouter(prefix="/ai/rag", tags=["rag"])

rag_ingestion_service = RAGIngestionService()


@router.post("/ingest", response_model=RAGIngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_document(
    file: UploadFile | None = File(default=None),
    text: str | None = Form(default=None),
    user_id: str | None = Form(default=None),
    document_id: str | None = Form(default=None),
    source: str = Form(default="rag_upload"),
    filename: str | None = Form(default=None),
) -> RAGIngestResponse:
    """Ingest an uploaded file or raw text into the reusable RAG vector store."""
    try:
        if file is not None and text is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either file or text, not both",
            )

        if file is not None:
            return rag_ingestion_service.ingest_upload(
                upload_file=file,
                user_id=user_id,
                document_id=document_id,
                source=source,
            )

        if text is not None:
            resolved_filename = filename or "content.txt"
            return rag_ingestion_service.ingest_text_content(
                text=text,
                user_id=user_id,
                document_id=document_id,
                source=source,
                filename=resolved_filename,
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either file or text to ingest",
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
