"""Text extraction per document type (SPEC.md §5 Pipeline RAG - Ingesta)."""
import io

import pdfplumber
from docx import Document as DocxDocument


def extract_text(content: bytes, doc_type: str) -> str:
    if doc_type == "pdf":
        return _extract_pdf(content)
    if doc_type == "docx":
        return _extract_docx(content)
    if doc_type == "txt":
        return content.decode("utf-8", errors="replace")
    raise ValueError(f"Unsupported document type for text extraction: {doc_type}")


def _extract_pdf(content: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def _extract_docx(content: bytes) -> str:
    doc = DocxDocument(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)
