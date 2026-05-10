"""Ingest a PDF into the reusable RAG pipeline and optionally verify retrieval.

Usage:
  python sample_rag_pdf_ingest.py --pdf-path C:/path/to/file.pdf --user-id demo_user
  python sample_rag_pdf_ingest.py --pdf-path C:/path/to/file.pdf --user-id demo_user --query "What is this document about?"
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

from app.rag.ingestion.document_loader import DocumentLoader
from app.rag.ingestion.indexer import Indexer
from app.rag.retrieval.retriever import Retriever


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("sample_rag_pdf_ingest")


def ingest_pdf(
    pdf_path: Path,
    user_id: str | None,
    document_id: str,
    source: str,
) -> list[dict[str, Any]]:
    loader = DocumentLoader()
    indexer = Indexer()

    logger.info("Loading PDF path=%s", pdf_path)
    text = loader.load_pdf_file(str(pdf_path))
    if not text.strip():
        raise ValueError(f"No extractable text found in PDF: {pdf_path}")

    logger.info("Indexing document_id=%s source=%s user_id=%s", document_id, source, user_id)
    chunks = indexer.index_document(
        document_id=document_id,
        source=source,
        text=text,
        user_id=user_id,
    )

    logger.info("Indexed %s chunks", len(chunks))
    return [chunk.model_dump() for chunk in chunks]


def verify_retrieval(query: str, user_id: str | None, top_k: int) -> None:
    retriever = Retriever()
    results = retriever.retrieve(query=query, user_id=user_id, top_k=top_k)
    logger.info("Retrieved %s chunks for query=%r", len(results), query)
    for idx, chunk in enumerate(results, start=1):
        logger.info(
            "Result #%s chunk_id=%s document_id=%s score=%.4f source=%s",
            idx,
            chunk.chunk_id,
            chunk.document_id,
            chunk.score,
            chunk.source,
        )
        logger.info("Content preview: %s", chunk.text[:250].replace("\n", " "))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest a PDF into Qdrant for RAG testing")
    parser.add_argument("--pdf-path", required=True, help="Path to the PDF document")
    parser.add_argument(
        "--user-id",
        default=None,
        help="Optional user scope for the stored vectors",
    )
    parser.add_argument(
        "--document-id",
        default=None,
        help="Optional document identifier. Defaults to the PDF stem.",
    )
    parser.add_argument(
        "--source",
        default="local_pdf",
        help="Human-readable source label stored in vector payloads",
    )
    parser.add_argument(
        "--query",
        default=None,
        help="Optional query to run after ingestion for a quick retrieval check",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of chunks to retrieve when verifying the ingestion",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pdf_path = Path(args.pdf_path).expanduser().resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    document_id = args.document_id or pdf_path.stem
    ingest_pdf(
        pdf_path=pdf_path,
        user_id=args.user_id,
        document_id=document_id,
        source=args.source,
    )

    if args.query:
        verify_retrieval(query=args.query, user_id=args.user_id, top_k=args.top_k)

    logger.info("PDF ingestion complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
