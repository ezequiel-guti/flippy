"""Tests de extracción de metadatos (SPEC_RAG.md §6)."""
import json

from app.integrations import gemini
from app.modules.documents import metadata as metadata_module
from app.modules.documents.metadata import extract_metadata


def _mock_response(payload: dict):
    return json.dumps(payload)


class TestDeterministicPass:
    def test_extracts_date_from_filename_iso(self, monkeypatch):
        monkeypatch.setattr(gemini, "generate_text", lambda prompt: _mock_response({}))
        result = extract_metadata("texto de prueba", "Reporte_2026-06-22_PBA.pdf")
        assert result.fecha_vigencia == "2026-06-22"
        assert result.confianza["fecha_vigencia"] == "alta"

    def test_no_date_in_filename_falls_back_to_model(self, monkeypatch):
        monkeypatch.setattr(
            gemini, "generate_text", lambda prompt: _mock_response({"fecha_vigencia": "2026-05-01"})
        )
        result = extract_metadata("texto de prueba", "reporte_mercado.pdf")
        assert result.fecha_vigencia == "2026-05-01"

    def test_extracts_spanish_month_abbreviation_no_separator(self, monkeypatch):
        monkeypatch.setattr(gemini, "generate_text", lambda prompt: _mock_response({}))
        result = extract_metadata("texto", "Planilla_Rubros_mod.11-REFORMAS.BANO_Mar2026.pdf")
        assert result.fecha_vigencia == "2026-03-01"

    def test_extracts_spanish_month_full_name_with_separator(self, monkeypatch):
        monkeypatch.setattr(gemini, "generate_text", lambda prompt: _mock_response({}))
        result = extract_metadata("texto", "Listado_de_materiales_y_mano_de_obra_julio_2026.pdf")
        assert result.fecha_vigencia == "2026-07-01"

    def test_iso_date_takes_priority_over_spanish_month(self, monkeypatch):
        monkeypatch.setattr(gemini, "generate_text", lambda prompt: _mock_response({}))
        result = extract_metadata("texto", "reporte_2026-06-22_Abr2026.pdf")
        assert result.fecha_vigencia == "2026-06-22"


class TestVocabularioCerrado:
    def test_valid_tipo_is_kept(self, monkeypatch):
        monkeypatch.setattr(gemini, "generate_text", lambda prompt: _mock_response({"tipo": "dato_mercado"}))
        result = extract_metadata("texto", "doc.pdf")
        assert result.tipo == "dato_mercado"

    def test_invalid_tipo_normalizes_to_none(self, monkeypatch):
        monkeypatch.setattr(gemini, "generate_text", lambda prompt: _mock_response({"tipo": "costos"}))
        result = extract_metadata("texto", "doc.pdf")
        assert result.tipo is None

    def test_invalid_region_normalizes_to_none(self, monkeypatch):
        monkeypatch.setattr(gemini, "generate_text", lambda prompt: _mock_response({"region": "Cordoba"}))
        result = extract_metadata("texto", "doc.pdf")
        assert result.region is None

    def test_invalid_moneda_normalizes_to_none(self, monkeypatch):
        monkeypatch.setattr(gemini, "generate_text", lambda prompt: _mock_response({"moneda": "EUR"}))
        result = extract_metadata("texto", "doc.pdf")
        assert result.moneda is None

    def test_null_moneda_stays_none(self, monkeypatch):
        monkeypatch.setattr(gemini, "generate_text", lambda prompt: _mock_response({"moneda": None}))
        result = extract_metadata("texto", "doc.pdf")
        assert result.moneda is None


class TestConfianzaBaja:
    def test_low_confidence_field_marks_needs_review(self, monkeypatch):
        monkeypatch.setattr(
            gemini,
            "generate_text",
            lambda prompt: _mock_response({"tipo": "costo", "confianza": {"tipo": "baja"}}),
        )
        result = extract_metadata("texto", "doc.pdf")
        assert result.needs_review is True

    def test_high_confidence_does_not_mark_needs_review(self, monkeypatch):
        monkeypatch.setattr(
            gemini,
            "generate_text",
            lambda prompt: _mock_response({"tipo": "costo", "confianza": {"tipo": "alta"}}),
        )
        result = extract_metadata("texto", "doc.pdf")
        assert result.needs_review is False


class TestModelFailure:
    def test_model_error_falls_back_to_needs_review(self, monkeypatch):
        def _raise(prompt):
            raise gemini.GeminiError(500, "internal error")

        monkeypatch.setattr(gemini, "generate_text", _raise)
        result = extract_metadata("texto", "doc.pdf")
        assert result.needs_review is True
        assert result.tipo is None

    def test_unparsable_response_falls_back_to_needs_review(self, monkeypatch):
        monkeypatch.setattr(gemini, "generate_text", lambda prompt: "esto no es JSON")
        result = extract_metadata("texto", "doc.pdf")
        assert result.needs_review is True

    def test_model_wraps_json_in_code_fence_still_parses(self, monkeypatch):
        monkeypatch.setattr(
            gemini, "generate_text", lambda prompt: f"```json\n{_mock_response({'tipo': 'costo'})}\n```"
        )
        result = extract_metadata("texto", "doc.pdf")
        assert result.tipo == "costo"


class TestPromptTruncation:
    def test_document_is_truncated_to_3000_tokens(self, monkeypatch):
        captured = {}

        def _capture(prompt):
            captured["prompt"] = prompt
            return _mock_response({})

        monkeypatch.setattr(gemini, "generate_text", _capture)
        huge_text = "palabra " * 10000
        extract_metadata(huge_text, "doc.pdf")
        tokens_in_prompt = len(metadata_module._encoding.encode(captured["prompt"]))
        # el prompt entero (instrucciones + documento truncado) debe quedar
        # razonablemente acotado, no crecer con el tamaño del documento
        assert tokens_in_prompt < 3500
