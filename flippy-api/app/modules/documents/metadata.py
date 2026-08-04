"""Extracción de metadatos tipados para filtrado por intención (SPEC_RAG.md §6).

Dos pasadas: determinística (nombre de archivo) primero — barata y exacta donde
aplica — y vía modelo (Gemini) para los campos que la primera no resuelve.
Un valor incorrecto es peor que null (§6.4): un campo dudoso se persiste igual,
pero marca needs_review para revisión manual en el panel de admin.
"""
import json
import logging
import re
from dataclasses import dataclass, field

import tiktoken

from app.integrations import gemini

logger = logging.getLogger(__name__)

_encoding = tiktoken.get_encoding("cl100k_base")

TIPO_VALUES = {
    "dato_mercado",
    "costo",
    "metodologia",
    "tecnica_construccion",
    "normativa",
    "caso_estudio",
    "faq",
    "otro",
}
MONEDA_VALUES = {"ARS", "USD"}
REGION_VALUES = {"CABA", "GBA_Norte", "GBA_Sur", "GBA_Oeste", "PBA", "Interior", "Nacional"}

PROMPT_TEMPLATE = """Extraé metadatos estructurados del siguiente documento del corpus inmobiliario.

Devolvé únicamente un objeto JSON, sin backticks, sin preámbulo, sin explicación.

Campos:
- fecha_vigencia: fecha a la que refieren los datos en formato YYYY-MM-DD.
  Si el documento reporta datos de un mes, usá el primer día de ese mes.
  Distinguí la fecha de los DATOS de la fecha de PUBLICACIÓN: prevalece la
  de los datos. Si no hay fecha determinable, null.
- tipo: uno de [dato_mercado, costo, metodologia, tecnica_construccion,
  normativa, caso_estudio, faq, otro].
- moneda: ARS, USD o null si el documento no expresa valores monetarios.
- region: una de [CABA, GBA_Norte, GBA_Sur, GBA_Oeste, PBA, Interior,
  Nacional] o null.
- es_primaria: true si el documento proviene de la fuente original del dato
  (organismo, colegio profesional, autor de la metodología). false si es
  comentario, resumen o análisis de terceros.
- confianza: objeto con nivel (alta / media / baja) por cada campo anterior
  que no sea null.

Cuando un campo no sea determinable con la información presente, usá null.
Inferir un valor plausible pero no sustentado es peor que devolver null:
un metadato incorrecto hace que el chunk se filtre mal y quede invisible
para consultas donde sí era relevante.

DOCUMENTO:
{documento}
"""


@dataclass
class ExtractedMetadata:
    fecha_vigencia: str | None = None
    tipo: str | None = None
    moneda: str | None = None
    region: str | None = None
    es_primaria: bool = False
    confianza: dict = field(default_factory=dict)
    needs_review: bool = False


_FILENAME_DATE_RE = re.compile(
    r"(?:(?P<y1>\d{4})[-_](?P<m1>\d{2})[-_](?P<d1>\d{2}))"
    r"|(?:(?P<d2>\d{2})[-_](?P<m2>\d{2})[-_](?P<y2>\d{4}))"
)


def _deterministic_fecha_from_filename(filename: str) -> str | None:
    match = _FILENAME_DATE_RE.search(filename)
    if not match:
        return None
    if match.group("y1"):
        y, m, d = match.group("y1"), match.group("m1"), match.group("d1")
    else:
        y, m, d = match.group("y2"), match.group("m2"), match.group("d2")
    try:
        if not (1 <= int(m) <= 12 and 1 <= int(d) <= 31):
            return None
    except ValueError:
        return None
    return f"{y}-{m}-{d}"


def _first_n_tokens(text: str, n: int) -> str:
    ids = _encoding.encode(text)
    return _encoding.decode(ids[:n])


def _normalize(value, allowed: set[str]) -> str | None:
    if value is None:
        return None
    if value in allowed:
        return value
    logger.warning("Valor de metadato fuera de vocabulario cerrado: %r (permitidos: %s)", value, sorted(allowed))
    return None


def _parse_model_response(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(json)?", "", cleaned).rsplit("```", 1)[0].strip()
    return json.loads(cleaned)


def extract_metadata(text: str, filename: str) -> ExtractedMetadata:
    deterministic_fecha = _deterministic_fecha_from_filename(filename)

    try:
        prompt = PROMPT_TEMPLATE.format(documento=_first_n_tokens(text, 3000))
        raw = gemini.generate_text(prompt)
        parsed = _parse_model_response(raw)
    except Exception:
        logger.exception("Extracción de metadatos vía modelo falló para %s", filename)
        return ExtractedMetadata(
            fecha_vigencia=deterministic_fecha,
            needs_review=True,
        )

    confianza = parsed.get("confianza") or {}
    tipo = _normalize(parsed.get("tipo"), TIPO_VALUES | {"otro"})
    moneda = _normalize(parsed.get("moneda"), MONEDA_VALUES)
    region = _normalize(parsed.get("region"), REGION_VALUES)
    fecha_vigencia = deterministic_fecha or parsed.get("fecha_vigencia")
    es_primaria = bool(parsed.get("es_primaria", False))

    fields_present = [f for f, v in (("fecha_vigencia", fecha_vigencia), ("tipo", tipo), ("moneda", moneda), ("region", region)) if v is not None]
    needs_review = any(confianza.get(f) == "baja" for f in fields_present)
    if deterministic_fecha:
        # la pasada determinística resolvió la fecha con certeza — no depende del modelo
        confianza["fecha_vigencia"] = "alta"

    return ExtractedMetadata(
        fecha_vigencia=fecha_vigencia,
        tipo=tipo,
        moneda=moneda,
        region=region,
        es_primaria=es_primaria,
        confianza=confianza,
        needs_review=needs_review,
    )
