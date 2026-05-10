"""Document ingestion service for the reusable RAG layer."""

from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import BinaryIO

from fastapi import UploadFile

from app.core.logger import get_logger
from app.rag.ingestion.document_loader import DocumentLoader
from app.rag.ingestion.indexer import Indexer
from app.rag.schemas import RAGIngestResponse

logger = get_logger(__name__)


class RAGIngestionService:
    """Ingest documents and raw text into the reusable vector store."""

    def __init__(
        self,
        loader: DocumentLoader | None = None,
        indexer: Indexer | None = None,
    ) -> None:
        self._loader = loader or DocumentLoader()
        self._indexer = indexer or Indexer()

    def ingest_upload(
        self,
        upload_file: UploadFile,
        user_id: str | None = None,
        document_id: str | None = None,
        source: str = "file_upload",
    ) -> RAGIngestResponse:
        """Persist an uploaded file to a temp path and index it into Qdrant."""
        filename = upload_file.filename or "uploaded_file"
        temp_path = self._save_upload_to_temp_file(upload_file.file, filename=filename)
        try:
            resolved_document_id = document_id or Path(filename).stem or "uploaded_document"
            logger.info(
                "rag_ingest_started filename=%s document_id=%s source=%s user_id=%s",
                filename,
                resolved_document_id,
                source,
                user_id,
            )

            text = self._loader.load_file(str(temp_path))
            if not text.strip():
                raise ValueError("No extractable text found in uploaded file")

            return self._index_and_respond(
                document_id=resolved_document_id,
                filename=filename,
                source=source,
                text=text,
                user_id=user_id,
            )
        finally:
            temp_path.unlink(missing_ok=True)

    def ingest_pdf_upload(
        self,
        upload_file: UploadFile,
        user_id: str | None = None,
        document_id: str | None = None,
        source: str = "pdf_upload",
    ) -> RAGIngestResponse:
        """Backward-compatible alias for PDF-focused callers."""
        return self.ingest_upload(
            upload_file=upload_file,
            user_id=user_id,
            document_id=document_id,
            source=source,
        )

    def ingest_text_content(
        self,
        text: str,
        user_id: str | None = None,
        document_id: str | None = None,
        source: str = "text_input",
        filename: str = "content.txt",
    ) -> RAGIngestResponse:
        """Index a raw text payload without requiring a file upload."""
        normalized_text = text.strip()
        if not normalized_text:
            raise ValueError("Text content cannot be empty")

        resolved_document_id = document_id or Path(filename).stem or "text_document"
        return self._index_and_respond(
            document_id=resolved_document_id,
            filename=filename,
            source=source,
            text=normalized_text,
            user_id=user_id,
        )

    def _index_and_respond(
        self,
        document_id: str,
        filename: str,
        source: str,
        text: str,
        user_id: str | None,
    ) -> RAGIngestResponse:
        """Index the provided text and build a consistent ingest response."""
        logger.info(
            "rag_ingest_indexing document_id=%s filename=%s source=%s user_id=%s",
            document_id,
            filename,
            source,
            user_id,
        )
        chunks = self._indexer.index_document(
            document_id=document_id,
            source=source,
            text=text,
            user_id=user_id,
        )
        chunk_ids = [chunk.chunk_id for chunk in chunks]

        logger.info(
            "rag_ingest_completed filename=%s document_id=%s chunks=%s user_id=%s",
            filename,
            document_id,
            len(chunks),
            user_id,
        )
        return RAGIngestResponse(
            document_id=document_id,
            filename=filename,
            source=source,
            user_id=user_id,
            chunk_count=len(chunks),
            chunk_ids=chunk_ids,
        )

    def _save_upload_to_temp_file(self, file_obj: BinaryIO, filename: str) -> Path:
        """Write an uploaded file stream to a temporary path for parsing."""
        suffix = Path(filename).suffix or ".bin"
        with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
            shutil.copyfileobj(file_obj, temp_file)
            return Path(temp_file.name)
