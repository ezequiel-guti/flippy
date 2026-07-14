"""Text extraction per document type (SPEC.md §5 Pipeline RAG - Ingesta)."""
import io
import json

import pdfplumber
from bs4 import BeautifulSoup
from docx import Document as DocxDocument


def extract_text(content: bytes, doc_type: str) -> str:
    if doc_type == "pdf":
        return _extract_pdf(content)
    if doc_type == "docx":
        return _extract_docx(content)
    if doc_type == "txt":
        return content.decode("utf-8", errors="replace")
    if doc_type == "json":
        return _extract_json(content)
    if doc_type == "html":
        return _extract_html(content)
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


def _extract_json(content: bytes) -> str:
    data = json.loads(content.decode("utf-8", errors="replace"))
    return json.dumps(data, ensure_ascii=False, indent=2)


def _extract_html(content: bytes) -> str:
    soup = BeautifulSoup(content.decode("utf-8", errors="replace"), "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator="\n\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n\n".join(lines)
