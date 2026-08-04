# RAG_SPEC.md

**Proyecto:** Flippy — `flippy-api`
**Ámbito:** Pipeline de ingesta, chunking, embeddings y recuperación
**Versión:** 1.0
**Relación con el Documento de Proyecto v2:** esta spec **extiende y corrige** la sección 5 del documento firmado. Ver §9 (Delta) para el detalle de qué cambia.

> **Para Claude Code:** este archivo es la fuente de verdad del módulo RAG. Si el Documento de Proyecto v2 y este archivo entran en conflicto sobre chunking, embeddings o recuperación, gana este archivo. Referenciarlo explícitamente al trabajar en `app/ingestion/` o `app/rag/`.

---

## 1. Estrategias de chunking

### 1.1 Principio rector

**Un chunk es la unidad mínima de texto que se sostiene sola al leerse fuera de su documento de origen.**

Test de validación: si para entender el chunk hace falta el párrafo anterior, el corte está mal. Este criterio prevalece sobre cualquier tamaño objetivo en tokens.

### 1.2 Enum `chunking_strategy`

```python
from enum import Enum

class ChunkingStrategy(str, Enum):
    ATOMIC      = "atomic"       # documento completo = 1 chunk
    BY_SECTION  = "by_section"   # corte por encabezados jerárquicos
    BY_TOPIC    = "by_topic"     # transcripciones, corte por cambio temático
    BY_QA_PAIR  = "by_qa_pair"   # 1 chunk = 1 par pregunta-respuesta
    FIXED_500   = "fixed_500"    # fallback: ventana fija con overlap
```

### 1.3 Tabla de asignación

| Estrategia | Cuándo aplica | Tamaño objetivo | Overlap | Corte duro |
|---|---|---|---|---|
| `ATOMIC` | Artículos de mercado, notas de prensa, tablas de costos, informes de una sola unidad argumentativa | 200–1.400 tokens | 0 | Si supera 1.400 → degradar a `BY_SECTION` |
| `BY_SECTION` | Manuales, guías metodológicas, documentos con encabezados Markdown/Word | 400–700 tokens | 50 | Sección >900 tokens → subdividir por párrafo respetando el encabezado padre |
| `BY_TOPIC` | Transcripciones de clases, videos, audios | 600–800 tokens | 100 | Corte en frontera de oración, nunca a mitad |
| `BY_QA_PAIR` | FAQs, documentos con formato pregunta/respuesta | Variable | 0 | Par >1.200 tokens → tratar la respuesta con `BY_SECTION` |
| `FIXED_500` | Fallback cuando ninguna heurística aplica | 500 tokens | 50 | Corte por frontera de párrafo, nunca a mitad de oración |

### 1.4 Router de despacho

La estrategia se resuelve en dos niveles:

1. **Explícita** — el admin la selecciona en el panel al subir el archivo. Siempre gana.
2. **Inferida** — si el admin no elige, se aplica la heurística de `infer_strategy()`.

```python
def infer_strategy(text: str, filename: str, mime_type: str) -> ChunkingStrategy:
    """
    Heurística de inferencia. Orden de evaluación importa:
    va de la señal más específica a la más genérica.
    """
    token_count = count_tokens(text)

    # 1. Patrón Q&A: >=3 líneas que terminan en '?' seguidas de texto
    if detect_qa_pattern(text):
        return ChunkingStrategy.BY_QA_PAIR

    # 2. Transcripción: marcas de tiempo o nombre de archivo indicativo
    if detect_timestamps(text) or re.search(r'(transcrip|clase|webinar|audio)', filename, re.I):
        return ChunkingStrategy.BY_TOPIC

    # 3. Documento corto y con estructura de artículo → atómico
    if token_count <= 1400 and count_headings(text) <= 1:
        return ChunkingStrategy.ATOMIC

    # 4. Estructura jerárquica detectable
    if count_headings(text) >= 2:
        return ChunkingStrategy.BY_SECTION

    # 5. Fallback
    return ChunkingStrategy.FIXED_500
```

> **Nota de implementación:** `infer_strategy()` debe loguear la estrategia elegida y la razón en la tabla `documents` (campo `strategy_reason`). Sin ese log, depurar un problema de recuperación seis semanas después es adivinanza.

---

## 2. Migración de base de datos

```sql
-- ============================================================
-- Migración 002: soporte de chunking por estrategia + metadatos tipados
-- ============================================================

-- 2.1 Enum de estrategia
CREATE TYPE chunking_strategy AS ENUM (
    'atomic', 'by_section', 'by_topic', 'by_qa_pair', 'fixed_500'
);

-- 2.2 Columnas nuevas en documents
ALTER TABLE documents
    ADD COLUMN strategy        chunking_strategy NOT NULL DEFAULT 'fixed_500',
    ADD COLUMN strategy_source text NOT NULL DEFAULT 'inferred'
        CHECK (strategy_source IN ('explicit', 'inferred')),
    ADD COLUMN strategy_reason text,
    ADD COLUMN token_count     integer,
    ADD COLUMN indexed_at      timestamptz;

-- 2.3 Metadatos tipados en document_chunks
-- Se mantiene metadata jsonb para datos no consultables,
-- pero los campos usados en filtrado pasan a columnas nativas.
ALTER TABLE document_chunks
    ADD COLUMN fecha_vigencia date,
    ADD COLUMN tipo           text,
    ADD COLUMN moneda         text CHECK (moneda IN ('ARS', 'USD') OR moneda IS NULL),
    ADD COLUMN region         text,
    ADD COLUMN es_primaria    boolean DEFAULT false,
    ADD COLUMN header_text    text,
    ADD COLUMN token_count    integer;

-- 2.4 Índices de pre-filtrado
CREATE INDEX idx_chunks_fecha    ON document_chunks (fecha_vigencia DESC NULLS LAST);
CREATE INDEX idx_chunks_tipo     ON document_chunks (tipo);
CREATE INDEX idx_chunks_region   ON document_chunks (region);
CREATE INDEX idx_chunks_primaria ON document_chunks (es_primaria) WHERE es_primaria = true;

-- Índice compuesto para la consulta más frecuente: datos de mercado recientes
CREATE INDEX idx_chunks_mercado
    ON document_chunks (tipo, region, fecha_vigencia DESC)
    WHERE tipo IN ('dato_mercado', 'costo');

-- 2.5 Índice vectorial
-- CAMBIO RESPECTO AL DOCUMENTO v2: HNSW en lugar de IVFFlat.
-- Razón en §2.6.
DROP INDEX IF EXISTS idx_chunks_embedding;
CREATE INDEX idx_chunks_embedding
    ON document_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

### 2.6 Por qué HNSW y no IVFFlat

El Documento v2 especifica IVFFlat. Conviene revisarlo por dos motivos concretos:

1. **IVFFlat degrada con pre-filtrado.** El índice particiona el espacio en listas y visita solo `probes` de ellas. Al aplicar un `WHERE` restrictivo antes (que es exactamente lo que hace el filtrado por intención de §7), muchas de esas listas quedan vacías tras el filtro y el recall cae de forma difícil de diagnosticar. HNSW tolera mucho mejor este patrón.
2. **IVFFlat requiere datos previos para entrenarse.** Hay que crear el índice *después* de cargar un volumen representativo, y reconstruirlo si el corpus crece mucho. Con un panel de administración donde el cliente sube documentos de forma continua, eso es una tarea de mantenimiento que nadie va a recordar hacer.

Costo del cambio: HNSW consume más memoria y su construcción es más lenta. A 250 MB de corpus (~60k–120k chunks) es irrelevante. En Supabase Pro entra sin problema.

**Esto es una desviación del documento firmado.** No cambia alcance ni precio, pero conviene registrarla (ver §9).

---

## 3. Contrato de las funciones de chunking

### 3.1 Modelo de datos

```python
from dataclasses import dataclass, field
from datetime import date

@dataclass
class Chunk:
    content: str                      # texto crudo del fragmento
    chunk_index: int                  # posición ordinal en el documento
    header_text: str | None = None    # prefijo de enriquecimiento (§4)
    token_count: int = 0
    metadata: dict = field(default_factory=dict)  # no consultable

    # Metadatos tipados — se propagan a columnas nativas
    fecha_vigencia: date | None = None
    tipo: str | None = None
    moneda: str | None = None
    region: str | None = None
    es_primaria: bool = False

    @property
    def embeddable_text(self) -> str:
        """Texto que efectivamente se vectoriza. Ver §4."""
        if self.header_text:
            return f"{self.header_text}\n\n{self.content}"
        return self.content
```

### 3.2 Firma común

Todas las funciones de chunking respetan la misma firma. Esto permite que el router las despache de forma uniforme.

```python
from typing import Protocol

class ChunkerFn(Protocol):
    def __call__(self, text: str, doc_meta: DocumentMeta) -> list[Chunk]: ...
```

```python
CHUNKERS: dict[ChunkingStrategy, ChunkerFn] = {
    ChunkingStrategy.ATOMIC:     chunk_atomic,
    ChunkingStrategy.BY_SECTION: chunk_by_section,
    ChunkingStrategy.BY_TOPIC:   chunk_by_topic,
    ChunkingStrategy.BY_QA_PAIR: chunk_by_qa_pair,
    ChunkingStrategy.FIXED_500:  chunk_fixed,
}

def chunk_document(text: str, doc_meta: DocumentMeta) -> list[Chunk]:
    strategy = doc_meta.strategy or infer_strategy(text, doc_meta.filename, doc_meta.mime_type)
    chunks = CHUNKERS[strategy](text, doc_meta)
    return [enrich_with_header(c, doc_meta) for c in chunks]
```

### 3.3 Invariantes que toda función debe cumplir

Estas condiciones se verifican en tests. Si alguna falla, el documento no se indexa y `status` pasa a `error`.

1. `chunk_index` es contiguo desde 0, sin huecos.
2. Ningún chunk tiene `content` vacío o solo espacios.
3. Ningún chunk supera 1.400 tokens en `embeddable_text` (límite operativo, no del modelo).
4. La concatenación de todos los `content` sin overlap cubre ≥95% del texto original. Pérdida mayor indica bug en el parser.
5. Ningún corte cae a mitad de una oración, salvo en `FIXED_500` cuando un párrafo excede el tamaño de ventana.

---

## 4. Header enrichment

### 4.1 Qué es

El texto que se envía al modelo de embeddings **no** es el chunk crudo, sino el chunk precedido por un encabezado de contexto. Esto eleva el recall de forma sustancial en consultas con filtro temporal o geográfico, que en este dominio son la mayoría.

### 4.2 Formato exacto

```
[Fuente: {nombre_documento} | Fecha: {fecha_vigencia} | Tipo: {tipo} | Región: {region}]

{contenido del chunk}
```

Campos ausentes se omiten junto con su separador. Nunca se emite `Fecha: None`.

**Ejemplo real** (a partir del artículo de escrituras de PBA):

```
[Fuente: Reporte Inmobiliario — Freno en escrituras de PBA | Fecha: 2026-06-22 | Tipo: dato_mercado | Región: PBA]

Durante mayo se registraron 9.068 compraventas de inmuebles en la provincia
de Buenos Aires, según el relevamiento mensual del Colegio de Escribanos...
```

### 4.3 Reglas

- El header se guarda por separado en `document_chunks.header_text`.
- `content` guarda el texto **sin** el header.
- Al construir el prompt para el modelo de chat se envía `content` a secas — el header es un artefacto de recuperación, no de generación. Enviarlo introduce ruido y arrastra el modelo a mencionar fuentes, algo que el criterio de aceptación "sin citas visibles" prohíbe explícitamente.
- El header cuenta contra el límite de 1.400 tokens del chunk.

---

## 5. Generación de embeddings

### 5.1 Parámetros

| Parámetro | Valor | Nota |
|---|---|---|
| Modelo | `text-embedding-3-small` | Sin cambios respecto a v2 |
| Dimensiones | 1536 | Default del modelo |
| Batch size | 128 chunks por request | Ver §5.2 |
| Límite duro de la API | 2.048 inputs / 8.191 tokens por input | No alcanzable con chunks de 1.400 |
| Reintentos | 5, backoff exponencial 1s→32s | Solo en 429 y 5xx |
| Timeout | 60s por request | |

### 5.2 Por qué 128 y no 2.048

El límite de la API es 2.048 inputs, pero conviene lotear más chico:

- Un fallo en un lote de 2.048 obliga a reprocesar 2.048 embeddings.
- Los lotes chicos permiten reportar progreso al panel de admin de forma granular.
- Con 128 chunks × ~1.000 tokens = ~128k tokens por request, ya se está cerca del límite práctico de tamaño de payload.

### 5.3 Implementación

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

BATCH_SIZE = 128

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=32),
    retry=retry_if_exception_type((RateLimitError, APIConnectionError, InternalServerError)),
)
async def embed_batch(texts: list[str]) -> list[list[float]]:
    resp = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    # La API preserva el orden de entrada, pero verificarlo es barato
    # y evita una clase entera de bugs silenciosos.
    assert len(resp.data) == len(texts)
    return [d.embedding for d in sorted(resp.data, key=lambda x: x.index)]


async def embed_chunks(chunks: list[Chunk], on_progress=None) -> list[Chunk]:
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        vectors = await embed_batch([c.embeddable_text for c in batch])
        for chunk, vec in zip(batch, vectors):
            chunk.embedding = vec
        if on_progress:
            await on_progress(min(i + BATCH_SIZE, len(chunks)), len(chunks))
    return chunks
```

### 5.4 Embedding de queries

Cada consulta del usuario genera su propio embedding antes de la búsqueda. Es 1 llamada de ~20 tokens: costo despreciable, pero suma 100–200 ms de latencia al primer token.

Optimización opcional (no para el hito 2): caché LRU de embeddings de query normalizada, con TTL de 24h. Solo vale la pena si el análisis de logs muestra repetición real de consultas.

### 5.5 Costo

| Concepto | Cálculo | Total |
|---|---|---|
| Corpus inicial 250 MB | ~60M tokens × USD 0,02/M | **~USD 1,20** (pago único) |
| Re-indexación completa | Idem | ~USD 1,20 por vez |
| Queries | ~20 tokens por consulta | < USD 0,01 / mes |

Consistente con la línea "< USD 1" del Documento v2 §8.1. El orden de magnitud se mantiene.

---

## 6. Extracción de metadatos

### 6.1 Estrategia de dos pasadas

Los metadatos **no** son automáticos y no se pueden inferir de forma confiable con regex sobre corpus heterogéneo. Se usan dos vías:

1. **Determinística** — cuando el formato es predecible (nombre de archivo con fecha, headers estructurados de NotebookLM). Barata y exacta.
2. **Vía modelo** — una llamada por documento que devuelve JSON estructurado. Se aplica cuando la vía 1 no resuelve todos los campos.

La vía 2 cuesta centavos por documento y ahorra trabajo manual al admin. Dado que el filtrado por intención (§7) depende enteramente de estos campos, hacerlo bien no es opcional.

### 6.2 Esquema de salida

```json
{
  "fecha_vigencia": "2026-06-22",
  "tipo": "dato_mercado",
  "moneda": "ARS",
  "region": "PBA",
  "es_primaria": true,
  "confianza": {
    "fecha_vigencia": "alta",
    "region": "alta",
    "moneda": "baja"
  }
}
```

### 6.3 Vocabulario cerrado

Sin vocabulario cerrado, el filtrado por intención no funciona: `WHERE tipo = 'costo'` no matchea contra `'costos'` ni `'precios de obra'`.

| Campo | Valores permitidos |
|---|---|
| `tipo` | `dato_mercado`, `costo`, `metodologia`, `tecnica_construccion`, `normativa`, `caso_estudio`, `faq`, `otro` |
| `moneda` | `ARS`, `USD`, `null` |
| `region` | `CABA`, `GBA_Norte`, `GBA_Sur`, `GBA_Oeste`, `PBA`, `Interior`, `Nacional`, `null` |
| `es_primaria` | `true` = fuente original (colegio, organismo, autor). `false` = derivada o comentario. |

Cualquier valor fuera del vocabulario se normaliza a `otro` / `null` y se loguea para revisión.

### 6.4 Prompt de extracción

```
Extraé metadatos estructurados del siguiente documento del corpus inmobiliario.

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
{primeros 3000 tokens del documento}
```

### 6.5 Manejo de baja confianza

Todo campo devuelto con `confianza: "baja"` se persiste pero se marca en `documents.needs_review = true`. El panel de administración muestra esos documentos en una vista aparte para corrección manual. Sin este circuito, los errores de extracción quedan enterrados hasta que alguien note una respuesta mal fechada.

---

## 7. Recuperación con filtrado por intención

### 7.1 Flujo

```
query del usuario
  → clasificación de intención (heurística + fallback a modelo)
  → construcción de cláusula WHERE
  → embedding de la query
  → búsqueda vectorial con pre-filtro
  → top-K chunks
```

### 7.2 Intenciones y su traducción a SQL

| Intención | Señales en la query | Filtro | Top-K |
|---|---|---|---|
| `precio_actual` | "cuánto vale", "precio hoy", "cotización", "m²" | `tipo IN ('dato_mercado','costo') AND fecha_vigencia > now() - interval '6 months'` | 5 |
| `costo_obra` | "cuánto sale", "presupuesto", "materiales", "mano de obra" | `tipo = 'costo' AND fecha_vigencia > now() - interval '4 months'` | 6 |
| `metodologia` | "cómo hago", "pasos", "sistema", "estrategia" | `tipo IN ('metodologia','caso_estudio')` | 5 |
| `tecnica` | "cómo se construye", "instalación", "materiales", "obra" | `tipo IN ('tecnica_construccion','metodologia')` | 5 |
| `normativa` | "permiso", "habilitación", "reglamento", "municipio" | `tipo = 'normativa'` | 4 |
| `general` | Sin señal clara | Sin filtro | 5 |

### 7.3 Ventana temporal — punto crítico

Los datos de mercado envejecen rápido. Un chunk con la cifra de compraventas de mayo 2026 es la respuesta correcta hoy y una respuesta equivocada dentro de ocho meses.

Regla: para intenciones `precio_actual` y `costo_obra`, la ventana temporal es **obligatoria**. Si el filtro devuelve menos de 3 chunks, se amplía progresivamente (6m → 12m → 24m → sin filtro) y **el chunk recuperado se acompaña de su fecha en el contexto enviado al modelo**, con instrucción explícita de advertir al usuario que el dato puede estar desactualizado.

Esto no viola el criterio de "sin citas visibles": advertir la antigüedad de un dato no es citar una fuente.

### 7.4 Consulta

```sql
SELECT
    dc.id,
    dc.content,
    dc.fecha_vigencia,
    dc.tipo,
    d.name AS document_name,
    1 - (dc.embedding <=> $1::vector) AS similarity
FROM document_chunks dc
JOIN documents d ON d.id = dc.document_id
WHERE d.status = 'ready'
  AND ($2::text[] IS NULL OR dc.tipo = ANY($2))
  AND ($3::date   IS NULL OR dc.fecha_vigencia >= $3)
  AND ($4::text   IS NULL OR dc.region IN ($4, 'Nacional'))
ORDER BY dc.embedding <=> $1::vector
LIMIT $5;
```

Notas:
- `region IN ($4, 'Nacional')` — una consulta sobre PBA también debe traer datos nacionales, que aplican por inclusión.
- Umbral mínimo de similitud: descartar resultados con `similarity < 0.25`. Un chunk irrelevante en el contexto es peor que un chunk menos.
- `SET hnsw.ef_search = 100` en la sesión antes de consultar, para elevar recall cuando hay pre-filtro activo.

### 7.5 Clasificación de intención

Primero heurística por keywords (barata, ~0 ms). Si ninguna intención supera el umbral, se cae a `general`. **No** se hace una llamada al modelo para clasificar en el hito 2: agrega latencia al primer token en la ruta caliente. Si la evaluación (§8) muestra que la heurística falla por encima del 20%, se reevalúa.

---

## 8. Set de evaluación

### 8.1 Por qué existe

Sin un set de evaluación, cualquier ajuste de tamaño de chunk, top-K o umbral de similitud es adivinanza. Con 30 preguntas anotadas hay señal suficiente para decidir con datos.

### 8.2 Estructura — `tests/eval/queries.json`

```json
[
  {
    "id": "q001",
    "query": "¿Cómo viene el mercado de escrituras en provincia de Buenos Aires?",
    "intent_expected": "precio_actual",
    "relevant_doc_names": ["Freno en escrituras de PBA"],
    "relevant_chunk_contains": ["9.068 compraventas", "descenso interanual del 23"],
    "notes": "Requiere que la cifra y su explicación (conflicto ARBA) estén en el mismo chunk o entre los recuperados."
  }
]
```

### 8.3 Cobertura mínima del set

| Categoría | Preguntas |
|---|---|
| Datos de mercado con filtro temporal | 6 |
| Costos de obra y materiales | 6 |
| Metodología de flipping | 6 |
| Técnicas constructivas | 4 |
| Normativa y permisos | 3 |
| Consultas ambiguas / generales | 3 |
| Fuera del corpus (debe responder "no tengo información") | 2 |

Las últimas 2 son las más importantes y las que casi siempre se omiten: verifican el criterio de aceptación "respuestas ancladas" del Documento v2 §10.

### 8.4 Métricas

```python
def evaluate(queries: list[EvalQuery], k: int = 5) -> EvalReport:
    """
    recall@k     — % de queries donde al menos un chunk relevante está en el top-k.
                   Métrica principal. Objetivo: >= 0.85
    mrr          — Mean Reciprocal Rank. Mide si el chunk correcto llega arriba.
                   Objetivo: >= 0.65
    intent_acc   — % de intenciones clasificadas correctamente. Objetivo: >= 0.80
    refusal_acc  — % de queries fuera de corpus donde no se recupera nada
                   por encima del umbral. Objetivo: 1.00
    """
```

### 8.5 Barrido de calibración

Ejecutar la evaluación contra las configuraciones que están en discusión, no contra una sola:

```
chunk_size: [300, 500, 800]  ×  top_k: [3, 5, 8]  ×  threshold: [0.20, 0.25, 0.30]
```

Se elige la combinación con mayor `recall@k` que no exceda 4.000 tokens de contexto RAG por consulta. El resultado del barrido se documenta en `docs/RAG_CALIBRATION.md` con fecha, para que la decisión sea auditable y no se relitigue.

### 8.6 Cuándo correrla

- Al cerrar el hito 2, antes de presentar al cliente.
- Tras cualquier cambio en estrategias de chunking o parámetros de recuperación.
- Tras cada carga masiva de corpus nuevo.

---

## 9. Delta contra el Documento de Proyecto v2

Cambios de esta spec respecto de lo documentado en la sección 5 del documento entregado a Virgilio.

| # | Documento v2 | Esta spec | Impacto | ¿Requiere aviso al cliente? |
|---|---|---|---|---|
| 1 | Chunks de 500 tokens uniformes | 5 estrategias según tipo de contenido | Mejora de calidad. Sin cambio de alcance ni precio. | No — es detalle de implementación |
| 2 | Overlap 50 tokens fijo | Variable (0–100 según estrategia) | Idem | No |
| 3 | Índice IVFFlat | Índice HNSW | Mayor consumo de memoria en Supabase. Sin impacto de costo al volumen actual. | **Sí** — es una decisión técnica explícita en el documento firmado |
| 4 | `metadata jsonb` genérico | Columnas tipadas + índices | Habilita el filtrado por intención | No |
| 5 | No contemplado | Header enrichment | Mejora de recall | No |
| 6 | No contemplado | Extracción de metadatos vía modelo | Suma ~USD 0,01 por documento al costo variable | No — despreciable |
| 7 | Top-K fijo en 5 | Variable 4–6 según intención | Idem | No |
| 8 | No contemplado | Set de evaluación de 30 preguntas | Suma ~1 día de trabajo dentro del hito 2 | No — absorbido en el hito |
| 9 | No contemplado | Advertencia de antigüedad en datos de mercado | Mejora funcional | No, pero conviene mencionarlo como valor agregado |

**Recomendación:** emitir un **v2.1** del documento de proyecto que actualice la sección 5 completa. No cambia hitos, montos ni plazos. El motivo real de emitirlo es que el documento firmado es lo que el cliente lee si algo sale mal; un documento que describe un pipeline distinto al implementado es una discusión evitable a futuro.

---

## 10. Checklist de implementación para el hito 2

- [ ] Migración 002 aplicada en Supabase (enum, columnas, índices, HNSW)
- [ ] `app/ingestion/chunking/` — 5 funciones + router + `infer_strategy()`
- [ ] Tests de invariantes de §3.3 (5 tests, uno por invariante)
- [ ] `enrich_with_header()` con formato exacto de §4.2
- [ ] `embed_chunks()` con batching, reintentos y callback de progreso
- [ ] Extractor de metadatos con vocabulario cerrado y flag `needs_review`
- [ ] Vista de "documentos a revisar" en el panel de admin
- [ ] Clasificador de intención heurístico + tabla de traducción a SQL
- [ ] Consulta de recuperación con pre-filtro y umbral de similitud
- [ ] `tests/eval/queries.json` con las 30 preguntas
- [ ] Script de evaluación con las 4 métricas
- [ ] Barrido de calibración ejecutado y documentado en `RAG_CALIBRATION.md`
- [ ] Selector de estrategia en el panel de subida de documentos

---

*Flippy — `flippy-api` · RAG_SPEC v1.0 · Botizar*