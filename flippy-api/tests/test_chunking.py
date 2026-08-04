"""Tests del router de chunking por estrategia (SPEC_RAG.md §1, §3.3)."""
import pytest

from app.modules.documents.chunking import (
    Chunk,
    ChunkingStrategy,
    DocumentMeta,
    chunk_atomic,
    chunk_by_qa_pair,
    chunk_by_section,
    chunk_by_topic,
    chunk_document,
    chunk_fixed,
    count_tokens,
    detect_qa_pattern,
    detect_timestamps,
    enrich_with_header,
    infer_strategy,
)

META = DocumentMeta(filename="documento.pdf", mime_type="application/pdf")

ATOMIC_TEXT = "Durante mayo se registraron 9.068 compraventas en la provincia de Buenos Aires, un descenso interanual del 23%."

SECTION_TEXT = """INTRODUCCIÓN

Este manual describe el proceso de flipping inmobiliario paso a paso, desde la búsqueda de la propiedad hasta la venta final.

1. BÚSQUEDA DE PROPIEDADES

""" + ("La búsqueda efectiva combina portales online, contactos con inmobiliarias locales y recorridas por el barrio objetivo. " * 40) + """

2. EVALUACIÓN DE COSTOS

""" + ("El presupuesto de reforma debe incluir materiales, mano de obra y un margen de contingencia del 15 al 20 por ciento. " * 40)

TOPIC_TEXT = (
    "00:00:05 Hoy vamos a hablar sobre técnicas de flipping. Es un tema central del curso. "
    "00:02:10 Primero, la búsqueda de la propiedad correcta. Hay que mirar ubicación y potencial. "
    "00:05:30 Segundo, el cálculo de costos de reforma. Nunca hay que subestimarlo. "
) * 5

QA_TEXT = """¿Cómo empiezo a hacer flipping?

Lo primero es definir un presupuesto claro y una zona objetivo.

¿Qué tipo de propiedades conviene buscar?

Propiedades con potencial de revalorización tras una reforma acotada.

¿Cuánto tiempo toma un proyecto típico?

Entre tres y seis meses desde la compra hasta la reventa."""

FIXED_TEXT = "\n\n".join(f"Párrafo número {i} sobre el mercado inmobiliario y sus variaciones regionales recientes." for i in range(80))


def _coverage_ratio(original: str, chunks) -> float:
    """Proxy de la cobertura del invariante §3.3.4: fracción de palabras del
    original que aparecen en la concatenación de todos los chunks."""
    original_words = set(original.lower().split())
    if not original_words:
        return 1.0
    chunk_words: set[str] = set()
    for c in chunks:
        chunk_words |= set(c.content.lower().split())
    return len(original_words & chunk_words) / len(original_words)


ALL_STRATEGY_SAMPLES = [
    (chunk_atomic, ATOMIC_TEXT),
    (chunk_by_section, SECTION_TEXT),
    (chunk_by_topic, TOPIC_TEXT),
    (chunk_by_qa_pair, QA_TEXT),
    (chunk_fixed, FIXED_TEXT),
]


@pytest.mark.parametrize("chunker,text", ALL_STRATEGY_SAMPLES)
def test_chunk_index_contiguous_from_zero(chunker, text):
    chunks = chunker(text, META)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


@pytest.mark.parametrize("chunker,text", ALL_STRATEGY_SAMPLES)
def test_no_chunk_is_empty(chunker, text):
    chunks = chunker(text, META)
    assert all(c.content.strip() for c in chunks)


@pytest.mark.parametrize("chunker,text", ALL_STRATEGY_SAMPLES)
def test_no_chunk_exceeds_1400_tokens(chunker, text):
    chunks = chunker(text, META)
    assert all(count_tokens(c.embeddable_text) <= 1400 for c in chunks)


@pytest.mark.parametrize("chunker,text", ALL_STRATEGY_SAMPLES)
def test_coverage_at_least_95_percent(chunker, text):
    chunks = chunker(text, META)
    assert _coverage_ratio(text, chunks) >= 0.95


def test_fixed_500_may_cut_paragraph_mid_sentence_when_oversized():
    huge_paragraph = "palabra " * 2000  # un solo párrafo, muy por encima de 500 tokens
    chunks = chunk_fixed(huge_paragraph, META)
    assert len(chunks) > 1
    assert all(count_tokens(c.content) <= 500 for c in chunks)


class TestInferStrategy:
    def test_detects_qa_pattern(self):
        strategy, reason = infer_strategy(QA_TEXT, "faq.pdf", "application/pdf")
        assert strategy == ChunkingStrategy.BY_QA_PAIR
        assert reason

    def test_detects_transcript_by_timestamps(self):
        strategy, _ = infer_strategy(TOPIC_TEXT, "clase.pdf", "application/pdf")
        assert strategy == ChunkingStrategy.BY_TOPIC

    def test_detects_transcript_by_filename(self):
        text = "Contenido sin marcas de tiempo pero con nombre indicativo. " * 30
        strategy, _ = infer_strategy(text, "Webinar_flipping_2026.pdf", "application/pdf")
        assert strategy == ChunkingStrategy.BY_TOPIC

    def test_short_document_is_atomic(self):
        strategy, _ = infer_strategy(ATOMIC_TEXT, "articulo.pdf", "application/pdf")
        assert strategy == ChunkingStrategy.ATOMIC

    def test_structured_document_is_by_section(self):
        strategy, _ = infer_strategy(SECTION_TEXT, "manual.pdf", "application/pdf")
        assert strategy == ChunkingStrategy.BY_SECTION

    def test_fallback_is_fixed_500(self):
        text = "oración larga sin estructura ni preguntas. " * 200
        strategy, _ = infer_strategy(text, "documento.pdf", "application/pdf")
        assert strategy == ChunkingStrategy.FIXED_500


class TestDetectors:
    def test_detect_qa_pattern_requires_at_least_three(self):
        assert not detect_qa_pattern("¿Una pregunta?\n\nRespuesta.")
        assert detect_qa_pattern(QA_TEXT)

    def test_detect_timestamps(self):
        assert detect_timestamps("00:01:23 texto 00:05:00 más texto")
        assert not detect_timestamps("sin marcas de tiempo acá")


class TestChunkDocument:
    def test_infers_when_no_explicit_strategy(self):
        result = chunk_document(ATOMIC_TEXT, META)
        assert result.strategy == ChunkingStrategy.ATOMIC
        assert result.strategy_source == "inferred"
        assert result.strategy_reason

    def test_respects_explicit_strategy(self):
        explicit_meta = DocumentMeta(filename="x.pdf", mime_type="application/pdf", strategy=ChunkingStrategy.FIXED_500)
        result = chunk_document(ATOMIC_TEXT, explicit_meta)
        assert result.strategy == ChunkingStrategy.FIXED_500
        assert result.strategy_source == "explicit"

    def test_empty_text_returns_no_chunks(self):
        result = chunk_document("   ", META)
        assert result.chunks == []


class TestEnrichWithHeader:
    def test_full_header_format(self):
        chunk = Chunk(content="texto", chunk_index=0, fecha_vigencia="2026-06-22", tipo="dato_mercado", region="PBA")
        enrich_with_header(chunk, "Reporte Inmobiliario — Freno en escrituras de PBA")
        assert chunk.header_text == (
            "[Fuente: Reporte Inmobiliario — Freno en escrituras de PBA | "
            "Fecha: 2026-06-22 | Tipo: dato_mercado | Región: PBA]"
        )

    def test_missing_fields_are_omitted_with_their_separator(self):
        chunk = Chunk(content="texto", chunk_index=0)  # sin fecha/tipo/region
        enrich_with_header(chunk, "Documento sin metadatos")
        assert chunk.header_text == "[Fuente: Documento sin metadatos]"
        assert "None" not in chunk.header_text
        assert "Fecha" not in chunk.header_text

    def test_content_never_carries_the_header(self):
        chunk = Chunk(content="texto del chunk", chunk_index=0, tipo="costo")
        enrich_with_header(chunk, "doc.pdf")
        assert chunk.content == "texto del chunk"
        assert "Fuente" not in chunk.content

    def test_embeddable_text_includes_header_content_alone_does_not(self):
        chunk = Chunk(content="texto del chunk", chunk_index=0, tipo="costo")
        enrich_with_header(chunk, "doc.pdf")
        assert chunk.header_text in chunk.embeddable_text
        assert chunk.embeddable_text != chunk.content
        assert chunk.content in chunk.embeddable_text

    def test_no_header_when_chunk_has_no_metadata_returns_fuente_only_never_empty(self):
        chunk = Chunk(content="texto", chunk_index=0)
        enrich_with_header(chunk, "x.pdf")
        assert chunk.header_text is not None  # Fuente siempre está disponible (nombre del documento)
