"""Recuperación con filtrado por intención (SPEC_RAG.md §7).

Re-ranking blando en vez de cascada de filtros duros (desviación de §7.4
documentada en DECISIONS.md, Incremento 18.7): el candidate pool se arma solo
por similitud, y tipo/fecha suman o restan puntaje en vez de excluir. La
cascada dura de §7.3 (filtrar por tipo, y si <3 resultados ampliar ventana
temporal 6→12→24→sin filtro) mostró en el eval real un patrón sistemático:
un chunk correcto y mejor rankeado por similitud quedaba afuera porque el
filtro de tipo lo excluía, o porque otros 3 chunks de *otro* documento con
fecha más reciente ya satisfacían el mínimo y cortaban el ensanchamiento
antes de llegar a él. Clasificación de intención heurística por keywords
(barata, ~0ms) — sin llamada a modelo en el hito 2 (§7.5).
"""
import json
from dataclasses import dataclass
from datetime import date

from app.core.db import get_db_connection

SIMILARITY_THRESHOLD = 0.40  # SPEC_RAG.md §7.4 fija 0.25; subido con evidencia real del
# eval (Incremento 18.6): los hits relevantes rankean en 0.55-0.68, el único falso
# positivo detectado rankeó en 0.32 — hay una banda vacía entre ambos.
HNSW_EF_SEARCH = 100
CANDIDATE_POOL_SIZE = 30
DAYS_PER_MONTH = 30  # aproximación suficiente para una ventana de "antigüedad de dato"

TIPO_BONUS = 0.15
MISSING_DATE_PENALTY = 0.03
STALE_PENALTY = 0.06
STALE_AGE_MULTIPLIER = 4  # más de (ventana base x 4) de antigüedad = penalización, no solo neutro


@dataclass
class Intent:
    name: str
    tipo_filter: list[str] | None
    top_k: int
    base_window_months: int | None = None  # None = sin noción de antigüedad para esta intención


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
        # "faq" incluido junto a metodologia/caso_estudio (Incremento 18.7) — la cápsula
        # de la comunidad ("La comunidad opina") extrae como faq (formato pregunta/
        # respuesta) y es, en la práctica, el contenido metodológico real del corpus.
        Intent("metodologia", ["metodologia", "caso_estudio", "faq"], top_k=5),
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


def _query_candidates(query_embedding: list[float], pool_size: int) -> list[dict]:
    """Candidate pool: solo similitud + estado 'ready'. Sin filtro de tipo/fecha —
    esos se aplican como puntaje en _score(), no como exclusión."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("set local hnsw.ef_search = %s", (HNSW_EF_SEARCH,))
            cur.execute(
                """
                select
                    dc.content,
                    dc.fecha_vigencia,
                    dc.tipo,
                    1 - (dc.embedding <=> %s::vector) as similarity
                from document_chunks dc
                join documents d on d.id = dc.document_id
                where d.status = 'ready'
                  and 1 - (dc.embedding <=> %s::vector) >= %s
                order by dc.embedding <=> %s::vector
                limit %s
                """,
                (
                    json.dumps(query_embedding),
                    json.dumps(query_embedding),
                    SIMILARITY_THRESHOLD,
                    json.dumps(query_embedding),
                    pool_size,
                ),
            )
            rows = cur.fetchall()
        conn.commit()
    finally:
        conn.close()

    return [{"content": r[0], "fecha_vigencia": r[1], "tipo": r[2], "similarity": r[3]} for r in rows]


def _within_window(fecha_vigencia: date | None, months: int, today: date) -> bool:
    if fecha_vigencia is None:
        return False
    return (today - fecha_vigencia).days <= months * DAYS_PER_MONTH


def _score(row: dict, intent: Intent, today: date) -> float:
    score = row["similarity"]

    if intent.tipo_filter and row["tipo"] in intent.tipo_filter:
        score += TIPO_BONUS

    if intent.base_window_months is not None:
        fecha = row["fecha_vigencia"]
        if fecha is None:
            score -= MISSING_DATE_PENALTY
        elif not _within_window(fecha, intent.base_window_months, today):
            age_days = (today - fecha).days
            if age_days > intent.base_window_months * DAYS_PER_MONTH * STALE_AGE_MULTIPLIER:
                score -= STALE_PENALTY
            # entre la ventana base y el límite de "muy viejo": neutro, ni bonus ni penalidad

    return score


def search(query: str, query_embedding: list[float]) -> tuple[list[str], bool]:
    """Retorna (textos de contexto, stale_notice). stale_notice=True cuando ningún
    chunk seleccionado tiene fecha dentro de la ventana base de la intención — en
    ese caso cada chunk con fecha conocida lleva su fecha anotada, para que el
    modelo pueda advertir que el dato podría estar desactualizado (§7.3)."""
    intent = classify_intent(query)
    candidates = _query_candidates(query_embedding, max(CANDIDATE_POOL_SIZE, intent.top_k * 5))
    if not candidates:
        return [], False

    today = date.today()
    ranked = sorted(candidates, key=lambda r: _score(r, intent, today), reverse=True)
    top = ranked[: intent.top_k]

    stale = intent.base_window_months is not None and not any(
        _within_window(r["fecha_vigencia"], intent.base_window_months, today) for r in top
    )

    contents = []
    for r in top:
        text = r["content"]
        if stale and r["fecha_vigencia"]:
            text = f"{text}\n(dato con fecha de vigencia: {r['fecha_vigencia']})"
        contents.append(text)

    return contents, stale
