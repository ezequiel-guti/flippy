"""Tests de clasificación de intención y re-ranking blando (SPEC_RAG.md §7)."""
import json
import pathlib
from datetime import date, timedelta

from app.modules.chat import retrieval
from app.modules.chat.retrieval import (
    GENERAL_INTENT,
    MAX_MERGED_CHUNKS,
    MAX_SUBQUERIES,
    Intent,
    SubQuery,
    _round_robin_merge,
    _score,
    _within_window,
    classify_intent,
    split_subqueries,
)


class TestClassifyIntent:
    def test_precio_actual(self):
        assert classify_intent("¿Cuánto vale el m² en Almagro?").name == "precio_actual"
        assert classify_intent("cuál es la cotización del dólar hoy").name == "precio_actual"

    def test_costo_obra(self):
        assert classify_intent("cuánto sale reformar un baño").name == "costo_obra"
        assert classify_intent("necesito un presupuesto de materiales").name == "costo_obra"

    def test_metodologia(self):
        assert classify_intent("¿cómo hago para empezar a invertir en flipping?").name == "metodologia"

    def test_tecnica(self):
        assert classify_intent("¿cómo se construye una losa?").name == "tecnica"

    def test_normativa(self):
        assert classify_intent("qué permiso necesito para reformar").name == "normativa"

    def test_general_fallback(self):
        assert classify_intent("hola, ¿cómo estás?").name == "general"

    def test_general_has_no_type_filter_and_no_temporal_window(self):
        intent = classify_intent("hola")
        assert intent.tipo_filter is None
        assert intent.base_window_months is None

    def test_precio_actual_and_costo_obra_prioritized_over_tecnica_materiales_overlap(self):
        # "materiales" está en costo_obra y tecnica; costo_obra va primero en la tabla §7.2
        assert classify_intent("necesito materiales para la obra").name == "costo_obra"

    def test_faq_is_a_valid_tipo_for_metodologia(self):
        intent = classify_intent("¿conviene comprar en primer piso?")
        assert intent.name == "metodologia"
        assert "faq" in intent.tipo_filter


class TestWithinWindow:
    TODAY = date(2026, 8, 4)

    def test_none_fecha_is_never_within_window(self):
        assert not _within_window(None, 6, self.TODAY)

    def test_recent_fecha_is_within_window(self):
        assert _within_window(self.TODAY - timedelta(days=10), 6, self.TODAY)

    def test_old_fecha_is_not_within_window(self):
        assert not _within_window(self.TODAY - timedelta(days=365), 6, self.TODAY)


class TestScore:
    TODAY = date(2026, 8, 4)
    COSTO_OBRA = Intent("costo_obra", ["costo"], top_k=6, base_window_months=4)

    def test_matching_tipo_gets_bonus(self):
        matching = {"similarity": 0.5, "tipo": "costo", "fecha_vigencia": None}
        other = {"similarity": 0.5, "tipo": "normativa", "fecha_vigencia": None}
        assert _score(matching, self.COSTO_OBRA, self.TODAY) > _score(other, self.COSTO_OBRA, self.TODAY)

    def test_missing_date_is_penalized_but_not_excluded(self):
        no_date = {"similarity": 0.5, "tipo": "costo", "fecha_vigencia": None}
        score = _score(no_date, self.COSTO_OBRA, self.TODAY)
        assert score < 0.5 + 0.15  # penalizado respecto al máximo posible (similarity + tipo bonus)
        assert score > 0  # nunca excluido — sigue siendo un candidato válido

    def test_recent_date_beats_missing_date_at_equal_similarity(self):
        recent = {"similarity": 0.5, "tipo": "costo", "fecha_vigencia": self.TODAY - timedelta(days=10)}
        no_date = {"similarity": 0.5, "tipo": "costo", "fecha_vigencia": None}
        assert _score(recent, self.COSTO_OBRA, self.TODAY) > _score(no_date, self.COSTO_OBRA, self.TODAY)

    def test_very_stale_date_is_penalized_more_than_missing_date(self):
        very_old = {"similarity": 0.5, "tipo": "costo", "fecha_vigencia": self.TODAY - timedelta(days=800)}
        no_date = {"similarity": 0.5, "tipo": "costo", "fecha_vigencia": None}
        assert _score(very_old, self.COSTO_OBRA, self.TODAY) < _score(no_date, self.COSTO_OBRA, self.TODAY)

    def test_general_intent_ignores_tipo_and_date(self):
        row = {"similarity": 0.5, "tipo": "costo", "fecha_vigencia": None}
        assert _score(row, GENERAL_INTENT, self.TODAY) == 0.5

    def test_high_similarity_can_still_outrank_a_bonus_without_it(self):
        # el punto del re-ranking blando: similitud alta pesa más que perder un bonus puntual
        strong_match_wrong_tipo = {"similarity": 0.68, "tipo": None, "fecha_vigencia": None}
        weak_match_right_tipo = {"similarity": 0.42, "tipo": "costo", "fecha_vigencia": self.TODAY}
        assert _score(strong_match_wrong_tipo, self.COSTO_OBRA, self.TODAY) > _score(
            weak_match_right_tipo, self.COSTO_OBRA, self.TODAY
        )


# Consulta real reportada por el cliente (comparativa contra NotebookLM): una sola
# pregunta enumerada que mezcla intenciones técnicas (enchufes, cañería, cable) con
# intenciones de costo (presupuesto, mano de obra). classify_intent devuelve una sola
# intención — "presupuesto" gana y fija costo_obra, dejando lo técnico sin recuperar.
COMPOUND_QUERY = """tengo que cambiar toda la instalacion electrica de un departamento de 60 anos en Saavedra
tiene 2 dormitorios, 1 bano, 55 m2
1. cuantos enchufes y donde?
2. Cuando cositos para prender la luz
3. Cuando m de caneria (y cual) y de cable?
4. Cuanto me cobraria un electricista por todo?
5. haceme listaod de materiales y presupuestos
6. algun electriciste recomendado por la comunidad?"""


class TestSplitSubqueries:
    def test_plain_question_is_not_split(self):
        subqueries = split_subqueries("¿cuánto sale reformar un baño?")
        assert [sq.text for sq in subqueries] == ["¿cuánto sale reformar un baño?"]

    def test_numbered_list_yields_one_subquery_per_item(self):
        assert len(split_subqueries(COMPOUND_QUERY)) == 6

    def test_preamble_is_prepended_to_every_numbered_item(self):
        subqueries = split_subqueries(COMPOUND_QUERY)
        # sin el preámbulo, "cuantos enchufes y donde?" pierde "instalacion electrica"
        # y "55 m2", que es lo que le da señal al embedding
        assert all("instalacion electrica" in sq.text for sq in subqueries)
        assert all("55 m2" in sq.text for sq in subqueries)

    def test_preamble_is_kept_out_of_the_text_used_to_classify_intent(self):
        """El preámbulo da contexto semántico al embedding, pero envenena la
        clasificación por keywords: "55 m2" contiene "m2", keyword de precio_actual,
        y sin esta separación las 6 sub-preguntas heredan esa intención y colapsan
        todas en la misma — verificado contra el corpus real."""
        subqueries = split_subqueries(COMPOUND_QUERY)
        assert not any("55 m2" in sq.intent_text for sq in subqueries)

    def test_sibling_items_do_not_all_collapse_into_one_intent(self):
        intents = {classify_intent(sq.intent_text).name for sq in split_subqueries(COMPOUND_QUERY)}
        assert len(intents) > 1

    def test_a_materials_item_is_classified_by_its_own_words(self):
        subqueries = split_subqueries(COMPOUND_QUERY)
        materiales = next(sq for sq in subqueries if "materiales" in sq.intent_text)
        assert classify_intent(materiales.intent_text).name == "costo_obra"

    def test_numbered_item_text_is_preserved_without_its_marker(self):
        subqueries = split_subqueries(COMPOUND_QUERY)
        assert any(sq.text.endswith("cuantos enchufes y donde?") for sq in subqueries)
        assert not any("1." in sq.text for sq in subqueries)

    def test_each_numbered_item_stays_in_its_own_subquery(self):
        subqueries = split_subqueries(COMPOUND_QUERY)
        enchufes = [sq for sq in subqueries if "enchufes" in sq.intent_text]
        assert len(enchufes) == 1
        assert "electricista" not in enchufes[0].intent_text

    def test_dash_bulleted_list_is_split(self):
        query = "quiero reformar la cocina\n- cuanto sale la mesada\n- que material conviene"
        assert len(split_subqueries(query)) == 2

    def test_a_single_enumerated_item_is_not_a_compound_question(self):
        subqueries = split_subqueries("reformar cocina\n1. cuanto sale")
        assert [sq.text for sq in subqueries] == ["reformar cocina\n1. cuanto sale"]

    def test_two_questions_in_one_line_are_split(self):
        subqueries = split_subqueries("¿cuántos enchufes pongo? ¿cuánto cable necesito?")
        assert len(subqueries) == 2
        assert any("enchufes" in sq.text for sq in subqueries)
        assert any("cable" in sq.text for sq in subqueries)

    def test_declarative_lead_in_becomes_preamble_of_every_question(self):
        subqueries = split_subqueries(
            "tengo un depto de 55 m2. ¿cuántos enchufes pongo? ¿cuánto cable necesito?"
        )
        assert all("55 m2" in sq.text for sq in subqueries)
        assert not any("55 m2" in sq.intent_text for sq in subqueries)

    def test_subquery_count_is_capped(self):
        """Sin tope, un mensaje con 200 ítems enumerados dispara 200 consultas a la
        base y un batch de embeddings desproporcionado — coste y latencia a merced
        de lo que escriba el usuario."""
        query = "reforma\n" + "\n".join(f"{i}. pregunta {i}" for i in range(1, 51))
        assert len(split_subqueries(query)) == MAX_SUBQUERIES

    def test_an_undivided_query_classifies_on_its_full_text(self):
        (subquery,) = split_subqueries("¿cuánto sale reformar un baño?")
        assert subquery.intent_text == subquery.text

    def test_no_eval_query_is_split(self):
        """Garantía de no-regresión: el split es conservador por diseño, ninguna de las
        30 queries del set de evaluación (§8) debe cambiar de comportamiento."""
        path = pathlib.Path(__file__).parent / "eval" / "queries.json"
        for q in json.loads(path.read_text(encoding="utf-8")):
            assert [sq.text for sq in split_subqueries(q["query"])] == [q["query"]], q["id"]


class TestRoundRobinMerge:
    def test_every_subquery_is_represented_before_any_gets_a_second_chunk(self):
        per_subquery = [
            [{"id": "a1", "content": "a1"}, {"id": "a2", "content": "a2"}],
            [{"id": "b1", "content": "b1"}],
        ]
        merged = _round_robin_merge(per_subquery, limit=3)
        assert [r["id"] for r in merged] == ["a1", "b1", "a2"]

    def test_duplicate_chunks_across_subqueries_are_kept_once(self):
        shared = {"id": "x", "content": "x"}
        per_subquery = [[shared], [shared, {"id": "y", "content": "y"}]]
        merged = _round_robin_merge(per_subquery, limit=10)
        assert [r["id"] for r in merged] == ["x", "y"]

    def test_merge_is_capped_at_the_limit(self):
        per_subquery = [[{"id": f"a{i}", "content": ""} for i in range(10)]]
        assert len(_round_robin_merge(per_subquery, limit=4)) == 4

    def test_a_single_subquery_keeps_its_original_order(self):
        rows = [{"id": "1", "content": ""}, {"id": "2", "content": ""}]
        assert _round_robin_merge([rows], limit=MAX_MERGED_CHUNKS) == rows

    def test_empty_result_sets_are_skipped(self):
        per_subquery = [[], [{"id": "b", "content": ""}], []]
        assert [r["id"] for r in _round_robin_merge(per_subquery, limit=5)] == ["b"]


class FakeCursor:
    """Doble del driver psycopg, no de la lógica: `search_multi` ejecuta su SQL real
    contra este cursor y recibe filas en el orden de columnas del SELECT."""

    def __init__(self, rows_by_call: list[list[tuple]], executed: list):
        self._rows_by_call = rows_by_call
        self._executed = executed
        self._calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        if "document_chunks" in sql:
            self._executed.append(params)
            self._rows = self._rows_by_call[self._calls] if self._calls < len(self._rows_by_call) else []
            self._calls += 1

    def fetchall(self):
        return self._rows


class FakeConnection:
    def __init__(self, rows_by_call):
        self._cursor = FakeCursor(rows_by_call, executed=[])
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        pass

    def close(self):
        self.closed = True


def _sub(text):
    """Sub-pregunta sin preámbulo: el texto que se embebe y el que clasifica coinciden."""
    return SubQuery(text, text)


def _row(chunk_id, content, tipo="costo", fecha=None, similarity=0.6):
    """Fila en el orden exacto del SELECT: id, content, fecha_vigencia, tipo, similarity."""
    return (chunk_id, content, fecha, tipo, similarity)


class TestSearchMulti:
    def test_chunks_from_every_subquery_reach_the_context(self, monkeypatch):
        conn = FakeConnection(
            [
                [_row("t1", "cañería de 3/4", tipo="tecnica_construccion")],
                [_row("c1", "mano de obra por boca", tipo="costo")],
            ]
        )
        monkeypatch.setattr(retrieval, "get_db_connection", lambda: conn)

        chunks, _stale = retrieval.search_multi(
            [_sub("cuántos m de cañería necesito"), _sub("cuánto sale el presupuesto")], [[0.1], [0.2]]
        )

        assert "cañería de 3/4" in chunks
        assert "mano de obra por boca" in chunks

    def test_one_query_is_run_per_subquery(self, monkeypatch):
        conn = FakeConnection([[], [], []])
        monkeypatch.setattr(retrieval, "get_db_connection", lambda: conn)

        retrieval.search_multi([_sub("a"), _sub("b"), _sub("c")], [[0.1], [0.2], [0.3]])

        assert conn._cursor._calls == 3

    def test_all_subqueries_share_a_single_connection(self, monkeypatch):
        conn = FakeConnection([[], []])
        opened = []

        def _open():
            opened.append(1)
            return conn

        monkeypatch.setattr(retrieval, "get_db_connection", _open)
        retrieval.search_multi([_sub("a"), _sub("b")], [[0.1], [0.2]])

        assert len(opened) == 1
        assert conn.closed

    def test_result_is_capped_at_max_merged_chunks(self, monkeypatch):
        # ids distintos por sub-pregunta: 6 sub-preguntas x top_k=5 = 30 chunks únicos
        many = [[_row(f"s{s}c{i}", f"chunk {s}-{i}") for i in range(10)] for s in range(6)]
        conn = FakeConnection(many)
        monkeypatch.setattr(retrieval, "get_db_connection", lambda: conn)

        chunks, _stale = retrieval.search_multi([_sub("q")] * 6, [[0.1]] * 6)

        assert len(chunks) == MAX_MERGED_CHUNKS

    def test_search_delegates_to_search_multi_and_is_unchanged_for_one_query(self, monkeypatch):
        conn = FakeConnection([[_row("x", "un solo chunk")]])
        monkeypatch.setattr(retrieval, "get_db_connection", lambda: conn)

        # intención 'general': sin ventana temporal, así que stale es False
        assert retrieval.search("hola", [0.1]) == (["un solo chunk"], False)

    def test_a_dateless_chunk_under_a_temporal_intent_still_raises_the_stale_notice(self, monkeypatch):
        """Comportamiento preexistente que search_multi no debe cambiar: costo_obra
        tiene ventana de 4 meses, y un chunk sin fecha no cae dentro de ella."""
        conn = FakeConnection([[_row("x", "presupuesto sin fecha", fecha=None)]])
        monkeypatch.setattr(retrieval, "get_db_connection", lambda: conn)

        assert retrieval.search("cuánto sale reformar", [0.1])[1] is True

    def test_a_stale_subquery_annotates_dates_and_raises_the_notice(self, monkeypatch):
        old = date.today() - timedelta(days=900)
        conn = FakeConnection([[_row("c1", "precio viejo", tipo="costo", fecha=old)]])
        monkeypatch.setattr(retrieval, "get_db_connection", lambda: conn)

        chunks, stale = retrieval.search_multi([_sub("cuánto sale la obra")], [[0.1]])

        assert stale
        assert str(old) in chunks[0]

    def test_no_candidates_yields_no_context(self, monkeypatch):
        conn = FakeConnection([[], []])
        monkeypatch.setattr(retrieval, "get_db_connection", lambda: conn)

        assert retrieval.search_multi([_sub("a"), _sub("b")], [[0.1], [0.2]]) == ([], False)
