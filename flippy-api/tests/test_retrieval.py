"""Tests de clasificación de intención y re-ranking blando (SPEC_RAG.md §7)."""
from datetime import date, timedelta

from app.modules.chat.retrieval import (
    GENERAL_INTENT,
    Intent,
    _score,
    _within_window,
    classify_intent,
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
