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
import re
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


# --- Preguntas compuestas (Incremento 19) -------------------------------------
# classify_intent() devuelve UNA intención: la primera que matchea en la tabla de
# prioridad. Una consulta real del cliente que enumera 6 sub-preguntas ("cuántos
# enchufes / cuánta cañería / cuánto cobra un electricista / hacé el presupuesto")
# contiene "presupuesto", cae entera en costo_obra, y el contenido técnico nunca
# se recupera aunque exista en el corpus. El riesgo ya estaba anotado en
# tests/eval/queries.json (q017). La solución es dividir la consulta y recuperar
# una vez por sub-pregunta.
#
# El split es deliberadamente conservador: solo dispara ante señales inequívocas
# de enumeración o ante 2+ preguntas. Ninguna de las 30 queries del set de
# evaluación (§8) lo dispara — hay un test que lo fija como invariante.
# 8 y no 12: con 12, la prueba contra el corpus real mostró que el margen extra se
# llenaba de chunks de otros rubros (revoques, contrapisos, carpintería) traídos por
# la sub-pregunta de "materiales y presupuestos". §7.4 — un chunk irrelevante en el
# contexto es peor que un chunk menos.
MAX_MERGED_CHUNKS = 8
MIN_SUBQUERIES = 2
# Tope duro: la cantidad de sub-preguntas la decide el texto del usuario, y cada una
# cuesta una consulta a la base. Sin tope, un mensaje con 200 ítems enumerados
# multiplica coste y latencia sin control.
MAX_SUBQUERIES = 8

_ENUM_LINE = re.compile(r"^[ \t]*(?:\d+[ \t]*[.)]|[-*•])[ \t]+", re.MULTILINE)
_AFTER_QUESTION_MARK = re.compile(r"(?<=\?)")


@dataclass(frozen=True)
class SubQuery:
    """Una sub-pregunta con sus dos textos, que NO son el mismo:

    - `text` (preámbulo + ítem) es lo que se embebe. El preámbulo lleva el contexto
      que el ítem solo no tiene: sin "instalación eléctrica... 55 m2", la frase
      "¿cuántos enchufes y dónde?" embebe contra el corpus entero.
    - `intent_text` (solo el ítem) es lo que clasifica la intención. Meter el
      preámbulo acá rompe la clasificación por keywords: "55 m2" contiene "m2",
      keyword de precio_actual, y las 6 sub-preguntas de la consulta real del
      cliente colapsaban todas en esa misma intención — que es justo lo que este
      incremento venía a evitar. Verificado contra el corpus real antes de separar.
    """

    text: str
    intent_text: str


def _sub_with_preamble(preamble: str, item: str) -> SubQuery:
    return SubQuery(text=f"{preamble}\n{item}" if preamble else item, intent_text=item)


def _split_enumerated(query: str) -> list[SubQuery]:
    markers = list(_ENUM_LINE.finditer(query))
    if len(markers) < MIN_SUBQUERIES:
        return []

    preamble = query[: markers[0].start()].strip()
    items = []
    for i, marker in enumerate(markers):
        end = markers[i + 1].start() if i + 1 < len(markers) else len(query)
        items.append(query[marker.end() : end].strip())
    return [_sub_with_preamble(preamble, item) for item in items if item]


def _split_questions(query: str) -> list[SubQuery]:
    if query.count("?") < MIN_SUBQUERIES:
        return []

    segments = [s.strip() for s in _AFTER_QUESTION_MARK.split(query)]
    questions = [s for s in segments if s.endswith("?")]
    if len(questions) < MIN_SUBQUERIES:
        return []

    opening = questions[0].find("¿")
    preamble = ""
    if opening > 0:
        preamble = questions[0][:opening].strip()
        questions[0] = questions[0][opening:]
    return [_sub_with_preamble(preamble, q) for q in questions]


def split_subqueries(query: str) -> list[SubQuery]:
    """Divide una consulta compuesta en sub-preguntas independientes.

    Sin señal clara de composición devuelve la consulta entera como una sola
    sub-pregunta (con `intent_text == text`) — el camino de la enorme mayoría de
    las consultas, idéntico al comportamiento previo al split."""
    subqueries = _split_enumerated(query) or _split_questions(query) or [SubQuery(query, query)]
    return subqueries[:MAX_SUBQUERIES]


def _round_robin_merge(per_subquery: list[list[dict]], limit: int) -> list[dict]:
    """Intercala los resultados de cada sub-pregunta en vez de ordenarlos por score
    global. Con orden global, las sub-preguntas de costo (scores más altos, corpus
    más denso) coparían el contexto y desplazarían a las técnicas — exactamente el
    bug que este incremento arregla. Round-robin garantiza que cada sub-pregunta
    aporte su mejor chunk antes de que ninguna aporte el segundo."""
    merged: list[dict] = []
    seen: set = set()
    depth = max((len(rows) for rows in per_subquery), default=0)

    for rank in range(depth):
        for rows in per_subquery:
            if rank >= len(rows):
                continue
            row = rows[rank]
            if row["id"] in seen:
                continue
            seen.add(row["id"])
            merged.append(row)
            if len(merged) == limit:
                return merged
    return merged


def classify_intent(query: str) -> Intent:
    q = query.lower()
    for intent, keywords in _INTENT_RULES:
        if any(kw in q for kw in keywords):
            return intent
    return GENERAL_INTENT


def _query_candidates(cur, query_embedding: list[float], pool_size: int) -> list[dict]:
    """Candidate pool: solo similitud + estado 'ready'. Sin filtro de tipo/fecha —
    esos se aplican como puntaje en _score(), no como exclusión.

    Recibe el cursor en vez de abrir conexión: con preguntas compuestas esto corre
    una vez por sub-pregunta y abrir N conexiones al pooler sería N veces la latencia
    de handshake antes del primer token."""
    cur.execute(
        """
        select
            dc.id,
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
    return [
        {"id": r[0], "content": r[1], "fecha_vigencia": r[2], "tipo": r[3], "similarity": r[4]}
        for r in cur.fetchall()
    ]


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


def _rank_for_subquery(cur, subquery: SubQuery, embedding: list[float], today: date) -> tuple[list[dict], bool]:
    """Recupera y rankea los chunks de UNA sub-pregunta con su propia intención.
    Retorna (top chunks, stale) — stale=True cuando ninguno cae dentro de la ventana
    temporal base de esa intención (§7.3)."""
    intent = classify_intent(subquery.intent_text)
    candidates = _query_candidates(cur, embedding, max(CANDIDATE_POOL_SIZE, intent.top_k * 5))
    if not candidates:
        return [], False

    ranked = sorted(candidates, key=lambda r: _score(r, intent, today), reverse=True)
    top = ranked[: intent.top_k]
    stale = intent.base_window_months is not None and not any(
        _within_window(r["fecha_vigencia"], intent.base_window_months, today) for r in top
    )
    return top, stale


def search_multi(subqueries: list[SubQuery], embeddings: list[list[float]]) -> tuple[list[str], bool]:
    """Recupera una vez por sub-pregunta y fusiona los resultados.

    Cada sub-pregunta se clasifica con su propia intención, así una consulta que
    mezcla "cuánta cañería" con "hacé el presupuesto" recupera contenido técnico Y
    de costo, en vez de que la primera keyword que matchee decida por toda la
    consulta. stale_notice es la disyunción: si alguna sub-pregunta tuvo que
    estirarse a datos viejos, el aviso se levanta para toda la respuesta (§7.3)."""
    today = date.today()
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("set local hnsw.ef_search = %s", (HNSW_EF_SEARCH,))
            results = [
                _rank_for_subquery(cur, subquery, embedding, today)
                for subquery, embedding in zip(subqueries, embeddings, strict=True)
            ]
        conn.commit()
    finally:
        conn.close()

    stale = any(is_stale for _top, is_stale in results)
    merged = _round_robin_merge([top for top, _is_stale in results], MAX_MERGED_CHUNKS)

    contents = []
    for r in merged:
        text = r["content"]
        if stale and r["fecha_vigencia"]:
            text = f"{text}\n(dato con fecha de vigencia: {r['fecha_vigencia']})"
        contents.append(text)

    return contents, stale


def search(query: str, query_embedding: list[float]) -> tuple[list[str], bool]:
    """Recuperación de una sola consulta — camino usado por la ruta de visión (F-04),
    donde el caption no se divide. La ruta de texto usa split_subqueries + search_multi."""
    return search_multi([SubQuery(query, query)], [query_embedding])
