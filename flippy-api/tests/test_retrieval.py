"""Tests de clasificación de intención y ventana temporal (SPEC_RAG.md §7)."""
from app.modules.chat.retrieval import _widen_steps, classify_intent


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


class TestWidenSteps:
    def test_precio_actual_base_6_months(self):
        assert _widen_steps(6) == [6, 12, 24, None]

    def test_costo_obra_base_4_months(self):
        assert _widen_steps(4) == [4, 12, 24, None]

    def test_always_ends_without_filter(self):
        assert _widen_steps(24)[-1] is None
