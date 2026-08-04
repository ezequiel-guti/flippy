"""Router de chunking por estrategia (SPEC_RAG.md §1, §3).

Extracción de texto (parsers.py) entrega texto plano — sin marcado
estructural real. `count_headings()` y `_looks_like_heading()` son por
lo tanto heurísticas sobre texto plano (líneas cortas, sin puntuación de
cierre, mayúsculas/numeración), no detección de encabezados Markdown/Word
verdaderos. Ver DECISIONS.md, Incremento 18.2.
"""
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

import tiktoken

_encoding = tiktoken.get_encoding("cl100k_base")


class ChunkingStrategy(str, Enum):
    ATOMIC = "atomic"
    BY_SECTION = "by_section"
    BY_TOPIC = "by_topic"
    BY_QA_PAIR = "by_qa_pair"
    FIXED_500 = "fixed_500"


@dataclass
class Chunk:
    content: str
    chunk_index: int
    header_text: str | None = None
    token_count: int = 0
    metadata: dict = field(default_factory=dict)

    fecha_vigencia: str | None = None
    tipo: str | None = None
    moneda: str | None = None
    region: str | None = None
    es_primaria: bool = False

    @property
    def embeddable_text(self) -> str:
        if self.header_text:
            return f"{self.header_text}\n\n{self.content}"
        return self.content


@dataclass
class DocumentMeta:
    filename: str
    mime_type: str
    strategy: ChunkingStrategy | None = None


class ChunkerFn(Protocol):
    def __call__(self, text: str, doc_meta: DocumentMeta) -> list[Chunk]: ...


@dataclass
class ChunkingResult:
    chunks: list[Chunk]
    strategy: ChunkingStrategy
    strategy_source: str  # 'explicit' | 'inferred'
    strategy_reason: str


def count_tokens(text: str) -> int:
    return len(_encoding.encode(text))


def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in text.split("\n\n") if p.strip()]


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _sentences(text: str) -> list[str]:
    flat = " ".join(_paragraphs(text))
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(flat) if s.strip()]


def detect_qa_pattern(text: str) -> bool:
    """>=3 párrafos terminados en '?' seguidos de un párrafo de contenido (§1.4.1).
    Opera a nivel párrafo, no línea cruda: parsers.py siempre entrega texto con
    párrafos separados por línea en blanco (ver docstring del módulo)."""
    paragraphs = _paragraphs(text)
    hits = sum(1 for p in paragraphs[:-1] if p.rstrip().endswith("?"))
    return hits >= 3


_TIMESTAMP_RE = re.compile(r"\b\d{1,2}:\d{2}(:\d{2})?\b")


def detect_timestamps(text: str) -> bool:
    return len(_TIMESTAMP_RE.findall(text)) >= 2


_NUMBERED_HEADING_RE = re.compile(r"^\d+(\.\d+)*[\.\)]?\s+\S")


def _looks_like_heading(paragraph: str) -> bool:
    if "\n" in paragraph or len(paragraph) > 80:
        return False
    stripped = paragraph.strip()
    if not stripped or stripped.endswith((".", "!", "?", ",", ";", ":")):
        return False
    if _NUMBERED_HEADING_RE.match(stripped):
        return True
    words = stripped.split()
    if len(words) >= 2 and stripped.upper() == stripped and any(c.isalpha() for c in stripped):
        return True
    return False


def count_headings(text: str) -> int:
    return sum(1 for p in _paragraphs(text) if _looks_like_heading(p))


def infer_strategy(text: str, filename: str, mime_type: str) -> tuple[ChunkingStrategy, str]:
    """Heurística de inferencia (SPEC_RAG.md §1.4). Orden de evaluación importa:
    va de la señal más específica a la más genérica."""
    token_count = count_tokens(text)

    if detect_qa_pattern(text):
        return ChunkingStrategy.BY_QA_PAIR, "detectado patrón Q&A (>=3 líneas terminadas en '?' seguidas de contenido)"

    if detect_timestamps(text) or re.search(r"(transcrip|clase|webinar|audio)", filename, re.I):
        return ChunkingStrategy.BY_TOPIC, "marcas de tiempo detectadas o nombre de archivo indicativo de transcripción"

    if token_count <= 1400 and count_headings(text) <= 1:
        return ChunkingStrategy.ATOMIC, f"documento corto ({token_count} tokens) sin estructura jerárquica"

    if count_headings(text) >= 2:
        return ChunkingStrategy.BY_SECTION, f"estructura jerárquica detectada ({count_headings(text)} encabezados)"

    return ChunkingStrategy.FIXED_500, "ninguna heurística aplicó (fallback)"


def _pack(units: list[str], sep: str, target_tokens: int, hard_max_tokens: int, overlap_tokens: int) -> list[str]:
    """Empaqueta `units` (párrafos u oraciones) en ventanas <= target_tokens,
    arrastrando `overlap_tokens` del final de una ventana a la siguiente.

    Si una unidad individual supera hard_max_tokens se fuerza un corte por
    tokens crudos (rompe oraciones) — únicamente red de seguridad para que
    ningún chunk exceda jamás el límite duro de 1.400 tokens del invariante
    §3.3.3; en el uso normal de BY_SECTION/BY_TOPIC/BY_QA_PAIR esto no debería
    activarse porque las unidades ya vienen pre-partidas por oración cuando
    hace falta.
    """
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    def flush() -> None:
        nonlocal current, current_tokens
        if not current:
            return
        chunks.append(sep.join(current))
        if overlap_tokens:
            carry: list[str] = []
            carry_tokens = 0
            for u in reversed(current):
                t = count_tokens(u)
                if carry and carry_tokens + t > overlap_tokens:
                    break
                carry.insert(0, u)
                carry_tokens += t
            current = carry
            current_tokens = carry_tokens
        else:
            current = []
            current_tokens = 0

    for unit in units:
        unit_tokens = count_tokens(unit)

        if unit_tokens > hard_max_tokens:
            flush()
            ids = _encoding.encode(unit)
            step = max(hard_max_tokens - overlap_tokens, 1)
            for i in range(0, len(ids), step):
                piece = _encoding.decode(ids[i : i + hard_max_tokens]).strip()
                # decode() then strip() can shift a boundary token (e.g. drops a
                # leading " word" token in favor of two shorter ones), occasionally
                # adding a token back — trim until the hard cap holds for real.
                while piece and count_tokens(piece) > hard_max_tokens:
                    piece = _encoding.decode(_encoding.encode(piece)[:-1]).strip()
                if piece:
                    chunks.append(piece)
            current, current_tokens = [], 0
            continue

        if current and current_tokens + unit_tokens > target_tokens:
            flush()

        current.append(unit)
        current_tokens += unit_tokens

    flush()
    return [c.strip() for c in chunks if c.strip()]


def chunk_atomic(text: str, doc_meta: DocumentMeta) -> list[Chunk]:
    content = text.strip()
    if not content:
        return []
    token_count = count_tokens(content)
    if token_count > 1400:
        return chunk_by_section(text, doc_meta)
    return [Chunk(content=content, chunk_index=0, token_count=token_count)]


def _split_by_heading(text: str) -> list[tuple[str | None, list[str]]]:
    paragraphs = _paragraphs(text)
    sections: list[tuple[str | None, list[str]]] = []
    heading: str | None = None
    body: list[str] = []

    for p in paragraphs:
        if _looks_like_heading(p):
            if heading is not None or body:
                sections.append((heading, body))
            heading, body = p, []
        else:
            body.append(p)

    if heading is not None or body:
        sections.append((heading, body))

    return sections or [(None, paragraphs)]


def chunk_by_section(text: str, doc_meta: DocumentMeta) -> list[Chunk]:
    chunks: list[Chunk] = []
    idx = 0

    for heading, body_paragraphs in _split_by_heading(text):
        if not body_paragraphs:
            continue
        for piece in _pack(body_paragraphs, sep="\n\n", target_tokens=700, hard_max_tokens=900, overlap_tokens=50):
            content = f"{heading}\n\n{piece}" if heading else piece
            chunks.append(Chunk(content=content, chunk_index=idx, token_count=count_tokens(content)))
            idx += 1

    return chunks or chunk_fixed(text, doc_meta)


def chunk_by_topic(text: str, doc_meta: DocumentMeta) -> list[Chunk]:
    sentences = _sentences(text)
    if not sentences:
        return []
    pieces = _pack(sentences, sep=" ", target_tokens=800, hard_max_tokens=1400, overlap_tokens=100)
    return [
        Chunk(content=piece, chunk_index=idx, token_count=count_tokens(piece)) for idx, piece in enumerate(pieces)
    ]


def _split_qa_pairs(text: str) -> list[tuple[str, str]]:
    paragraphs = _paragraphs(text)
    pairs: list[tuple[str, str]] = []
    i, n = 0, len(paragraphs)

    while i < n:
        if paragraphs[i].endswith("?"):
            question = paragraphs[i]
            i += 1
            answer_parts: list[str] = []
            while i < n and not paragraphs[i].endswith("?"):
                answer_parts.append(paragraphs[i])
                i += 1
            pairs.append((question, "\n\n".join(answer_parts)))
        else:
            i += 1

    return pairs


def chunk_by_qa_pair(text: str, doc_meta: DocumentMeta) -> list[Chunk]:
    pairs = _split_qa_pairs(text)
    if not pairs:
        return chunk_fixed(text, doc_meta)

    chunks: list[Chunk] = []
    idx = 0

    for question, answer in pairs:
        full = f"{question}\n\n{answer}" if answer else question
        token_count = count_tokens(full)

        if token_count <= 1200:
            chunks.append(Chunk(content=full, chunk_index=idx, token_count=token_count))
            idx += 1
            continue

        # Par >1.200 tokens: tratar la respuesta con BY_SECTION (SPEC_RAG.md §1.3)
        answer_paragraphs = [p for p in answer.split("\n\n") if p.strip()] or [answer]
        for piece in _pack(answer_paragraphs, sep="\n\n", target_tokens=700, hard_max_tokens=900, overlap_tokens=0):
            content = f"{question}\n\n{piece}"
            chunks.append(Chunk(content=content, chunk_index=idx, token_count=count_tokens(content)))
            idx += 1

    return chunks


def chunk_fixed(text: str, doc_meta: DocumentMeta) -> list[Chunk]:
    paragraphs = _paragraphs(text)
    if not paragraphs:
        return []
    pieces = _pack(paragraphs, sep="\n\n", target_tokens=500, hard_max_tokens=500, overlap_tokens=50)
    return [
        Chunk(content=piece, chunk_index=idx, token_count=count_tokens(piece)) for idx, piece in enumerate(pieces)
    ]


CHUNKERS: dict[ChunkingStrategy, ChunkerFn] = {
    ChunkingStrategy.ATOMIC: chunk_atomic,
    ChunkingStrategy.BY_SECTION: chunk_by_section,
    ChunkingStrategy.BY_TOPIC: chunk_by_topic,
    ChunkingStrategy.BY_QA_PAIR: chunk_by_qa_pair,
    ChunkingStrategy.FIXED_500: chunk_fixed,
}


def enrich_with_header(chunk: Chunk, document_name: str) -> Chunk:
    """Antepone el header de contexto (§4.2) — se usa solo en `embeddable_text`
    (vectorización), nunca en `content` ni en el prompt de chat (§4.3: el header
    es un artefacto de recuperación, enviarlo violaría "sin citas visibles").
    Campos ausentes se omiten junto con su separador; nunca se emite "Fecha: None"."""
    fields = [
        ("Fuente", document_name),
        ("Fecha", chunk.fecha_vigencia),
        ("Tipo", chunk.tipo),
        ("Región", chunk.region),
    ]
    parts = [f"{label}: {value}" for label, value in fields if value]
    chunk.header_text = f"[{' | '.join(parts)}]" if parts else None
    return chunk


def chunk_document(text: str, doc_meta: DocumentMeta) -> ChunkingResult:
    if doc_meta.strategy is not None:
        strategy, source, reason = doc_meta.strategy, "explicit", "seleccionada explícitamente por el admin"
    else:
        strategy, reason = infer_strategy(text, doc_meta.filename, doc_meta.mime_type)
        source = "inferred"

    chunks = CHUNKERS[strategy](text, doc_meta)
    return ChunkingResult(chunks=chunks, strategy=strategy, strategy_source=source, strategy_reason=reason)
