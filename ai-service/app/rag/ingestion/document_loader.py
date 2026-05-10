"""Document loading helpers for the reusable RAG ingestion pipeline."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


class DocumentLoader:
    """Loads source documents into raw text for downstream chunking."""

    def load_text_file(self, path: str) -> str:
        """Load a plain text file as UTF-8."""
        file_path = Path(path)
        return file_path.read_text(encoding="utf-8")

    def load_markdown_file(self, path: str) -> str:
        """Load a markdown file as UTF-8.

        Markdown is preserved as text for now; downstream chunking and
        generation can decide how much formatting to retain.
        """
        file_path = Path(path)
        return file_path.read_text(encoding="utf-8")

    def load_pdf_file(self, path: str) -> str:
        """Extract text from a PDF file without OCR.

        This loader is intentionally simple and deterministic. It is suitable
        for text-based PDFs and will skip pages that do not contain extractable
        text. OCR can be added later as a separate concern.
        """
        file_path = Path(path)
        reader = PdfReader(str(file_path))

        extracted_pages: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            page_text = page_text.strip()
            if page_text:
                extracted_pages.append(page_text)

        return "\n\n".join(extracted_pages)

    def load_file(self, path: str) -> str:
        """Load a supported file type based on its suffix."""
        suffix = Path(path).suffix.lower()
        if suffix in {".txt", ".text"}:
            return self.load_text_file(path)
        if suffix in {".md", ".markdown"}:
            return self.load_markdown_file(path)
        if suffix == ".pdf":
            return self.load_pdf_file(path)
        raise ValueError(f"Unsupported document type: {suffix or '<no extension>'}")
