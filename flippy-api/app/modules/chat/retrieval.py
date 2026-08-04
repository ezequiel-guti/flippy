"""Recuperación con filtrado por intención (SPEC_RAG.md §7).

Clasificación heurística por keywords (barata, ~0ms) — sin llamada a modelo
en el hito 2 (§7.5); si la evaluación (SPEC_RAG.md §8) muestra que la
heurística falla por encima del 20%, se reevalúa.
"""
import json
from dataclasses import dataclass
from datetime import date, timedelta

from app.core.db import get_db_connection

SIMILARITY_THRESHOLD = 0.25
HNSW_EF_SEARCH = 100
MIN_RESULTS_BEFORE_WIDENING = 3
DAYS_PER_MONTH = 30  # aproximación suficiente para una ventana de "antigüedad de dato"


@dataclass
class Intent:
    name: str
    tipo_filter: list[str] | None
    top_k: int
    base_window_months: int | None = None  # None = sin ventana temporal obligatoria


# Orden importa (§7.5): de la señal más específica a la más genérica.
# Listas ampliadas sobre las de la tabla original de SPEC_RAG.md §7.2 con variantes
# reales encontradas en tests/eval/queries.json — la tabla original solo cubría la
# frase literal ("cuánto sale") y fallaba con fraseo natural equivalente ("cuánto
# cuesta"). Ver DECISIONS.md, Incremento 18.6.
_INTENT_RULES: list[tuple[Intent, list[str]]] = [
    (
        Intent("precio_actual", ["dato_mercado", "costo"], top_k=5, base_window_months=6),
        [
            "cuánto vale", "cuanto vale", "precio hoy", "cotización", "cotizacion", "m²", "m2",
            "cómo viene el mercado", "como viene el mercado", "cómo está el mercado", "como esta el mercado",
            "compraventas", "escrituras", "valor promedio", "valores de venta",
        ],
    ),
    (
        Intent("costo_obra", ["costo"], top_k=6, base_window_months=4),
        [
            "cuánto sale", "cuanto sale", "presupuesto", "materiales", "mano de obra",
            "cuánto cuesta", "cuanto cuesta", "cuánto aumentó", "cuanto aumento", "costo de", "costo total",
        ],
    ),
    (
        Intent("metodologia", ["metodologia", "caso_estudio"], top_k=5),
        [
            "cómo hago", "como hago", "pasos", "sistema", "estrategia",
            "conviene", "cómo funciona", "como funciona",
        ],
    ),
    (
        Intent("tecnica", ["tecnica_construccion", "metodologia"], top_k=5),
        [
            "cómo se construye", "como se construye", "instalación", "instalacion", "materiales", "obra",
            "cuánto necesito", "cuanto necesito", "cómo se calcula", "como se calcula",
            "cómo se calculan", "como se calculan",
        ],
    ),
    (
        Intent("normativa", ["normativa"], top_k=4),
        [
            "permiso", "habilitación", "habilitacion", "reglamento", "municipio",
            "qué establece", "que establece", "cláusulas", "clausulas", "contrato", " ley ",
        ],
    ),
]

GENERAL_INTENT = Intent("general", tipo_filter=None, top_k=5)


def classify_intent(query: str) -> Intent:
    q = query.lower()
    for intent, keywords in _INTENT_RULES:
        if any(kw in q for kw in keywords):
            return intent
    return GENERAL_INTENT


def _widen_steps(base_months: int) -> list[int | None]:
    """6→12→24→sin filtro (§7.3), arrancando en la ventana base de cada intención
    en vez de siempre en 6 — costo_obra parte de 4 meses (§7.2), no de 6."""
    steps: list[int | None] = [base_months]
    for months in (12, 24):
        if months > steps[-1]:
            steps.append(months)
    steps.append(None)
    return steps


def _query_chunks(
    query_embedding: list[float], tipo_filter: list[str] | None, fecha_min: date | None, top_k: int
) -> list[dict]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("set local hnsw.ef_search = %s", (HNSW_EF_SEARCH,))
            cur.execute(
                """
                select
                    dc.content,
                    dc.fecha_vigencia,
                    1 - (dc.embedding <=> %s::vector) as similarity
                from document_chunks dc
                join documents d on d.id = dc.document_id
                where d.status = 'ready'
                  and (%s::text[] is null or dc.tipo = any(%s))
                  and (%s::date is null or dc.fecha_vigencia >= %s)
                  and 1 - (dc.embedding <=> %s::vector) >= %s
                order by dc.embedding <=> %s::vector
                limit %s
                """,
                (
                    json.dumps(query_embedding),
                    tipo_filter,
                    tipo_filter,
                    fecha_min,
                    fecha_min,
                    json.dumps(query_embedding),
                    SIMILARITY_THRESHOLD,
                    json.dumps(query_embedding),
                    top_k,
                ),
            )
            rows = cur.fetchall()
        conn.commit()
    finally:
        conn.close()

    return [{"content": r[0], "fecha_vigencia": r[1], "similarity": r[2]} for r in rows]


def search(query: str, query_embedding: list[float]) -> tuple[list[str], bool]:
    """Retorna (textos de contexto, stale_notice). stale_notice=True cuando hubo
    que ampliar la ventana temporal más allá de la inicial de la intención (§7.3)
    — en ese caso cada chunk con fecha conocida lleva su fecha anotada, para que
    el modelo pueda advertir que el dato podría estar desactualizado."""
    intent = classify_intent(query)

    if intent.base_window_months is None:
        rows = _query_chunks(query_embedding, intent.tipo_filter, None, intent.top_k)
        return [r["content"] for r in rows], False

    rows: list[dict] = []
    stale = False
    for step_index, months in enumerate(_widen_steps(intent.base_window_months)):
        fecha_min = None if months is None else date.today() - timedelta(days=months * DAYS_PER_MONTH)
        rows = _query_chunks(query_embedding, intent.tipo_filter, fecha_min, intent.top_k)
        if len(rows) >= MIN_RESULTS_BEFORE_WIDENING or months is None:
            stale = step_index > 0
            break

    contents = []
    for r in rows:
        text = r["content"]
        if stale and r["fecha_vigencia"]:
            text = f"{text}\n(dato con fecha de vigencia: {r['fecha_vigencia']})"
        contents.append(text)

    return contents, stale
