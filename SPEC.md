# SPEC.md — Flippy
**Versión:** 2.0
**Fecha:** 2026-06-30
**Cliente:** Virgilio
**Desarrollador:** Ezequiel Gutiérrez — Botizar
**Compliance Tier:** Tier 2 — Business
**Estado:** SPEC STATUS: APPROVED — aprobado por el desarrollador el 2026-07-05

---

## §A — Delta Log

| # | Fecha | Sección | Cambio | Motivo |
|---|-------|---------|--------|--------|
| 1 | 2026-06-30 | §5 | Arquitectura actualizada: backend separado en FastAPI Python (v1 era Next.js API Routes) | Documento v2.0 corrige stack |
| 2 | 2026-07-05 | §3, §5, §8, §9 | Split LLM propagado: routing texto→Gemini / imagen→Claude en F-02 y pipeline RAG; fila Gemini en costos; `GOOGLE_API_KEY` en secretos; caso de test de routing | Revisión de consistencia post-decisión LLM |
| 3 | 2026-07-12 | §C | Brand Token Sheet corregido: reemplaza valores [proposed] por valores [explicit] del brandbook formal del cliente (`docs/Flipping Master - Manual de Marca.pdf`), no revisado hasta este punto. Colores/logo/reglas de contraste ahora exactos | Documento de marca formal encontrado en docs/ tras haber aprobado una versión con gaps propuestos por el desarrollador |
| 4 | 2026-07-15 | §3 | F-03 ampliado: eliminar chat (menú kebab + modal de confirmación + comportamiento del chat activo) — la opción de renombrar ya estaba especificada pero nunca se había implementado ninguna de las dos; el ícono kebab del sidebar era decorativo | El usuario reportó no poder eliminar un chat; investigación confirmó que la funcionalidad nunca se construyó en frontend ni backend |
| 5 | 2026-07-17 | §3, §7 | F-04 implementado: bucket privado `chat-attachments` + URL firmada resuelta en cada lectura, streaming SSE (no "llamada estándar"). Modelo corregido de `claude-3-5-sonnet-20241022` (oct-2024, casi seguro retirado) a `claude-sonnet-5` — sin verificación en vivo por falta de `ANTHROPIC_API_KEY` | Mismo patrón de staleness ya visto con `gemini-2.0-flash` en el Incremento 7; corregido proactivamente en vez de esperar a que falle en producción |
| 6 | 2026-07-19 | §3 (F-08) | Íconos PWA generados (192/512/apple-touch), meta tags iOS en `layout.tsx`, banner de onboarding de instalación (`IOSInstallBanner.tsx`) | Auditoría de Hito 1 detectó `manifest.json` apuntando a archivos de ícono inexistentes — instalabilidad rota; y ausencia total del banner de onboarding iOS que F-08 punto 1 ya especificaba pero nunca se había construido |
| 7 | 2026-07-23 | §2, §6, §12 | OD-01 resuelta: el plan gratuito da acceso completo durante los primeros 6 meses desde el alta (`created_at`); vencidos, el acceso se bloquea por completo hasta que el usuario se suscriba. Nueva RN-07. Nueva OD-03 (interacción con `cancelado` de usuarios que sí llegaron a pagar) | Confirmado por Virgilio vía el desarrollador — límite de tipo temporal, no por cantidad de mensajes ni corpus reducido |
| 8 | 2026-07-24 | §3 (F-05), §4, §6 | Carpetas y subcarpetas para organizar documentos del corpus: nueva tabla `document_folders` (anidamiento ilimitado vía `parent_id`), `documents.folder_id`, RN-08 (solo administrador, no se puede eliminar una carpeta no vacía, sin impacto en el pipeline RAG) | Pedido directo del desarrollador para ordenar el corpus a medida que crece; confirmado que las carpetas son puramente organizativas y no deben tocar chunking/embeddings/retrieval |
| 9 | 2026-07-24 | §3 (F-05, punto 9) | Navegación de carpetas rediseñada de breadcrumb + grid a árbol lateral (sidebar), estilo file manager clásico (expandir/contraer subcarpetas, carpeta actual resaltada) | El desarrollador compartió una referencia visual de file manager (sidebar izquierdo para navegar carpetas) — se adaptó la estructura solicitada manteniendo la paleta de marca aprobada (§C, vino/marfil/Cormorant Garamond), no los colores del ejemplo |
| 10 | 2026-08-02 | §3 (F-05, punto 11), §6 (RN-06) | Reprocesar documento sin volver a subirlo: nuevo endpoint `POST /admin/documents/{id}/reprocess` que re-descarga el archivo desde Supabase Storage (`storage_path`), borra `document_chunks` existentes del documento y vuelve a correr el pipeline de ingesta; disponible en cualquier estado (`processing`\|`ready`\|`error`); botón ↻ junto al de eliminar en la tabla | El desarrollador consultó si un documento subido se puede reprocesar tras revisar el flujo actual (sin esa opción, solo permitía borrar y volver a subir) |
| 11 | 2026-08-02 | §6 (RN-06) | QA del incremento de reprocesar detectó y corrigió: (1) orden de operaciones — la descarga desde Storage ahora se confirma antes de borrar chunks/marcar `processing`, evitando que un documento quede trabado sin datos si la descarga falla; (2) sanitización del nombre de archivo al construir `storage_path` (previene path traversal vía `../`), aplicada en la subida y heredada por reprocess/delete | Hallazgos de `$qa` (Security Reviewer) sobre el propio incremento — el segundo era un patrón preexistente en upload/delete, corregido en origen con aprobación explícita del desarrollador antes de tocar el fix de seguridad |
| 12 | 2026-08-02 | §3 (F-05, punto 12), §4, §6 (RN-06) | Detalle de error de ingesta: nueva columna `documents.error_detail` (texto, nullable) que guarda el mensaje de la excepción cuando el procesamiento (inicial o reprocesamiento) falla; visible como tooltip sobre el badge "Error" en la tabla del panel admin | El desarrollador pidió investigar por qué un documento específico (`ddcb7017-...`) había quedado en estado error; la investigación reprodujo el pipeline completo sin fallas (descarga/extracción/chunking/embeddings, todos exitosos con el archivo real) y concluyó que fue una falla transitoria — pero no había forma de confirmarlo sin acceso a logs de Railway, porque `process_document` atrapaba la excepción sin persistir el mensaje en ningún lado |
| 13 | 2026-08-03 | §5 (pipeline de ingesta) | Fix — `extract_text` elimina caracteres NUL (`\x00`) del texto extraído antes de devolverlo, para los 5 tipos vectorizables | El fix de `error_detail` (delta #12) reveló, apenas desplegado, la causa real del documento en error investigado ese mismo día: `psycopg2.errors.UndefinedColumn` primero (migración no había llegado a la base real de Railway — ver Incremento 14.1) y, una vez resuelto eso, `error_detail = "A string literal cannot contain NUL (0x00) characters."` al reprocesar — el PDF real tenía bytes NUL embebidos que Postgres rechaza en columnas de texto |
| 14 | 2026-08-03 | §4, §5 | SPEC_RAG.md adoptada como spec del módulo RAG — extiende y corrige §5 completa: 5 estrategias de chunking (antes fixed 500/50 único), migración a columnas tipadas + HNSW (antes `metadata jsonb` + IVFFlat), header enrichment, extracción de metadatos vía modelo, recuperación con filtrado por intención (antes top-5 fijo sin filtro), set de evaluación de 30 preguntas. Detalle completo del delta en SPEC_RAG.md §9. Build en increments per SPEC_RAG.md §10 | El desarrollador confirmó construir SPEC_RAG.md como mejora sobre el pipeline ya implementado; sin cambio de alcance ni precio salvo el ítem HNSW ya señalado en SPEC_RAG.md §9 como aviso pendiente al cliente |
| 14 | 2026-08-03 | §3 (F-05, punto 13), §4 | Documentos colgados en `processing`: nueva columna `documents.processing_started_at`; el botón "Reprocesar" se habilita si ese estado lleva más de 10 minutos, en vez de quedar deshabilitado indefinidamente. Además, tabla de documentos: columnas Estado y Carpeta angostadas, tabla con `table-layout: fixed` al 100% del contenedor con scroll horizontal propio en vez de expandirse | Pedido directo del desarrollador tras notar documentos reales que quedaron en `processing` sin resolverse nunca, y que la tabla del panel admin se veía desproporcionada/empujaba el layout hacia la derecha |
| 15 | 2026-08-03 | Identidad visual (nuevo componente `LoadingSpinner`) | Los estados de carga de página completa (`/chat`, `/admin`) pasan de texto plano ("Cargando…") a un spinner con el escudo de Flippy (`/icons/logo-shield.png`) en el centro, anillo girando alrededor en color vino (`--color-primary`) | Pedido directo del desarrollador — reforzar la identidad de marca también en los estados de carga, no solo en headers y contenido |
| 16 | 2026-08-05 | §5 (pipeline de ingesta) | Fix — `embed_texts` se llama en lotes (`_embed_in_batches`, límite ~250k tokens y 500 ítems por request) en vez de mandar todos los chunks de un documento en un solo request a la API de embeddings de OpenAI | El desarrollador reportó que "Todo Flippy Remodelador.pdf" daba error al subir; `error_detail` mostró la causa exacta: OpenAI rechazó el request con "Requested 895504 tokens, max 300000 tokens per request" — el documento generó suficientes chunks para exceder el límite por request en una sola llamada sin loteo |
| 17 | 2026-08-05 | §3 (F-05, punto 12), §6 (RN-08) | UX: spinner + botones deshabilitados en `AdminFolderPanel` mientras se elimina una carpeta (antes no había ninguna señal de que la acción estuviera en curso); el mensaje de `error_detail` ahora se muestra directamente en la grilla de documentos junto al nombre del archivo (antes solo visible al pasar el mouse sobre el badge "Error") | El desarrollador reportó no saber si el click en "Eliminar" carpeta estaba haciendo algo, y pidió que el error de un PDF fallido fuera visible en la grilla sin depender de hover |
| 18 | 2026-08-05 | §3 (F-05, punto 6) | UX: spinner + botón deshabilitado en `AdminDocumentTable` mientras se elimina un documento — la fila ya no desaparece optimísticamente de la tabla al hacer click, se saca recién cuando el backend confirma el borrado | El desarrollador pidió el mismo tipo de feedback ya agregado para eliminar carpetas (delta #17), esta vez para documentos |
| 19 | 2026-08-06 | §1 | Agregada tabla "Hitos del proyecto" (Hito 1–4) con alcance y estado de cada uno — el rango "Hitos 1–4" ya figuraba en el CLAUDE.md del proyecto pero no estaba desglosado dentro de SPEC.md | El desarrollador pidió el detalle del Hito 4 (QA final, pruebas en dispositivos reales, transferencia de repositorios/entornos/cuentas al cliente), no documentado hasta este punto |
| 20 | 2026-08-06 | §5 (pipeline de chat), §7 | Fix — modelo Gemini corregido de `gemini-2.5-flash` a `gemini-flash-latest` en `app/integrations/gemini.py`. Google dejó de habilitar `gemini-2.5-flash` para proyectos/keys nuevos (`404 NOT_FOUND — "no longer available to new users"`), aunque el modelo siga listado por `ListModels` | El desarrollador rotó las tres API keys (Google/OpenAI/Anthropic) y el chat dejó de responder ("No pudimos generar una respuesta. Intenta de nuevo."). Investigación confirmó que la key nueva autentica correctamente contra Gemini, pero el modelo hardcodeado ya no está habilitado para ella; probado en vivo qué modelos sí responden 200 con la key nueva antes de elegir el reemplazo. Mismo patrón de staleness de modelo ya visto en los Incrementos 7 y 9.1 — tercera vez que una rotación/cambio externo de Google/Anthropic invalida un modelo hardcodeado |
| 21 | 2026-08-06 | §3 (F-02) | UX: burbuja vacía de la respuesta de Flippy reemplazada por un spinner mientras no llegó el primer chunk del streaming; agregado spinner de carga al cambiar de chat en el sidebar mientras se piden sus mensajes (`ChatMessage`/`ChatWindow`/`chat/page.tsx`) | El desarrollador reportó ver "una parte sin nada" abajo al cargar un mensaje y pidió un spinner mientras cargan los mensajes — la causa raíz de ambos reportes era la misma: la burbuja placeholder del assistant se agregaba con `content: ""` antes de recibir el primer chunk (`<p></p>` vacío, sin ninguna señal visual), y no había indicador al cambiar de chat mientras se pedía su historial |

---

## §C — Identidad Visual

**Material disponible:** Completo — brandbook formal (`docs/Flipping Master - Manual de Marca.pdf`) + prototipo de referencia (`docs/flippy_prototipo_v4_claro (1).html`), descubiertos en `docs/` el 2026-07-12 (no habían sido revisados antes de este punto — corrección de un Brand Token Sheet anterior basado en datos parciales/propuestos).
**Fuente:** Manual de Marca (Flipping Master) + prototipo HTML aprobado por el cliente
**Color primario:** `#8B2E3B` (Vino Flipping)
**Tipografía primaria:** Cormorant Garamond (títulos) — alt sistema: Georgia
**Brand Token Sheet status:** Approved — 2026-07-12 (fuente: brandbook formal, reemplaza versión anterior basada en gaps propuestos)

### BRAND TOKEN SHEET — Flippy (Flipping Master)
Source: Manual de Marca (PDF formal del cliente) + prototipo HTML v4
Prepared: 2026-07-12
Status: Approved — valores explícitos del brandbook, no requieren aprobación adicional

**COLOR TOKENS**

Core (regla de uso 55% negro / 30% blanco / 12% vino / 3% dorado)
```
--color-onyx:            #0E0E10   [explicit] — "Negro Onyx", sofisticación, dominante 55%
--color-white:            #FFFFFF   [explicit] — "Blanco Puro", dominante 30%
--color-primary:         #8B2E3B   [explicit] — "Vino Flipping", identidad/acciones, 12%
--color-gold:             #D4AF37   [explicit] — "Oro Metálico", acento CTA/premium, 3% — nunca como fondo dominante
```

Neutrals (escala cálida — combina mejor con el vino que grises fríos)
```
--color-bg:              #F4F1EC   [explicit] — "Marfil/Crema", fondo principal
--color-surface-alt:     #D9D6D1   [explicit] — "Gris Niebla", fondos de sección/tarjetas/separadores
--color-text-secondary:  #6E6E73   [explicit] — "Gris Piedra", texto secundario/captions/metadata
--color-text-primary:    #2B2B2D   [explicit] — "Gris Carbón", texto de cuerpo (más amable que negro puro)
```

Acentos complementarios (dosis pequeñas — nunca como fondo dominante)
```
--color-silver:          #C5C8CC   [explicit] — "Plata Platino", detalles modernos/foil
--color-navy:            #1B2A3A   [explicit] — "Azul Noche", contextos corporativos/financieros → usado como --color-info
--color-pine:            #1E3A30   [explicit] — "Verde Pino", estabilidad/crecimiento/ROI → usado como --color-success
```

Semantic (mapeo sobre acentos del brandbook; sin color de error explícito en el manual)
```
--color-success:         #1E3A30   [explicit] — Verde Pino (ROI, crecimiento)
--color-info:             #1B2A3A   [explicit] — Azul Noche (contextos institucionales)
--color-warning:          #D4AF37   [explicit] — Oro (uso moderado, no como fondo)
--color-error:            #B3261E   [proposed] — el manual no define rojo de error; propuesto por no competir con vino ni con los acentos
```

Reglas de contraste (del manual — obligatorias)
```
Permitido:  vino sobre marfil/blanco · marfil sobre vino · dorado sobre negro o vino
Evitar:     vino sobre negro (bajo contraste) · dorado sobre marfil (se pierde) · gris piedra sobre vino
```

**TYPOGRAPHY TOKENS**
```
--font-primary:         "Cormorant Garamond", Georgia, serif                    [explicit] — titulares, mayúsculas con tracking amplio
--font-secondary:       "Lato", Arial, Calibri, -apple-system, sans-serif       [explicit] — cuerpo, UI, formularios
--font-weight-light:    300   [explicit] — Lato Light para párrafos largos
--font-weight-regular:  400   [explicit] — Lato Regular para UI
--font-weight-bold:     700   [explicit] — Lato Bold para énfasis
--font-size-h1:         2rem      [proposed] — no especificado en pt/px por el manual
--font-size-h2:         1.5rem    [proposed]
--font-size-body:       1rem      [proposed]
--font-size-label:      0.875rem  [proposed]
```

**LOGO**
```
Versión color:      sobre fondos claros (marfil, blanco, gris niebla)   [explicit]
Versión blanca:      sobre fondos oscuros (negro, vino, azul noche)      [explicit]
Área de protección:  margen libre = altura del escudo                    [explicit]
Tamaño mínimo:       96px pantalla / 25mm impresión (lockup horizontal); por debajo, solo el escudo   [explicit]
Prohibido:           deformar, cambiar colores, usar sin contraste, rotar/inclinar   [explicit]
Archivo:             extraído del prototipo → flippy-web/public/icons/logo-shield.png (207×245px, placeholder hasta recibir exports oficiales del diseñador — falta versión cuadrada para íconos PWA 192/512)
```

**SPACING AND SHAPE**
```
--border-radius-sm:     6px    [inferred] — del prototipo (chips, botones pequeños)
--border-radius-md:     12px   [inferred] — del prototipo (inputs, botones primarios)
--border-radius-lg:     18px   [explicit] — del prototipo (.msg — burbujas de chat)
--border-radius-tail:   5px    [explicit] — del prototipo (esquina de "cola" en burbujas)
--spacing-unit:         8px    [proposed] — no especificado, consistente con el prototipo
```

**GAPS RESUELTOS**
- Color de error no definido en el manual → propuesto `#B3261E`, elegido por no competir visualmente con vino/oro/pino/azul noche
- Tamaños de fuente en px/rem no definidos (el manual da jerarquía cualitativa H1/H2/Cuerpo/Caption, no valores) → propuesta una escala estándar
- Logo cuadrado para íconos PWA (192×192, 512×512) no disponible — el shield extraído del prototipo es 207×245 (no cuadrado) → placeholder hasta recibir exports oficiales

**APROBACIÓN**
- [x] Tokens [explicit] — provienen del brandbook formal del cliente, no requieren aprobación adicional
- [x] Tokens [proposed]/[inferred] revisados y aprobados por el desarrollador — 2026-07-12
- [ ] Logo cuadrado oficial para íconos PWA (pendiente del diseñador del cliente)

---

## §1 — Visión y Objetivo

**Visión:** Flippy es la herramienta de consulta inteligente de la comunidad educativa inmobiliaria de Virgilio. Los usuarios obtienen respuestas precisas sobre el material del curso sin necesidad de buscar manualmente en documentos.

**Objetivo medible:** Permitir que cualquier miembro de la comunidad de Virgilio realice consultas en lenguaje natural sobre el corpus documental interno y reciba respuestas contextualizadas en menos de 5 segundos, sin exponer las fuentes subyacentes.

**Problema que resuelve:** El conocimiento de la comunidad está disperso en PDFs, Word y materiales de formación. Buscar manualmente es lento y el resultado depende de la habilidad del usuario. Flippy centraliza el acceso y lo convierte en conversación.

**Modelo de negocio:** Suscripción mensual recurrente vía Mercado Pago. Plan gratuito (funcionalidades limitadas, a definir) y plan pago (acceso completo).

**Hitos del proyecto** (Tier 2 Business · USD 4.300 · 6.5 semanas):

| Hito | Alcance | Estado |
|------|---------|--------|
| **Hito 1** | Estructura base de servicios (FastAPI + Next.js PWA), modelo de datos en Supabase, autenticación (F-01), deploy a Railway, PWA instalable (íconos, meta tags iOS, onboarding) | Completado |
| **Hito 2** | Pipeline de ingesta y panel de administración del corpus (F-05, con carpetas y reprocesamiento), chat RAG real con streaming (F-02), eliminar/renombrar chat (F-03), análisis de imagen (F-04) | Completado, en refinamiento continuo |
| **Hito 3** | Integración de pagos con Mercado Pago (F-06/F-07): suscripción recurrente, webhooks de estado, sandbox de pagos (flujo de suscripción, pago rechazado → mora → reintento → restauración), enforcement del límite de 6 meses del plan gratuito (RN-07) | No iniciado |
| **Hito 4** | QA final, pruebas rigurosas en dispositivos móviles reales (iPhone, Android, Chrome) y transferencia absoluta de repositorios, entornos y control de cuentas a la propiedad del cliente | No iniciado |

---

## §2 — Usuarios y Roles

| Rol | Descripción | Acceso |
|-----|-------------|--------|
| **Usuario gratuito** | Miembro registrado sin suscripción activa | Chat completo durante 6 meses desde el alta, luego bloqueado (RN-07) |
| **Usuario pago** | Miembro con suscripción mensual activa | Chat completo + análisis de imágenes |
| **Usuario en mora** | Suscripción con pago rechazado, reintentos en curso | Acceso degradado al límite del plan gratuito |
| **Usuario cancelado** | Suscripción cancelada definitivamente | Solo plan gratuito |
| **Administrador** | Ezequiel / operador de la comunidad | Panel de gestión de documentos del corpus |

**Nota:** No hay rol "superadmin" ni multi-tenancy. Un solo cliente, un solo corpus, una sola comunidad.

---

## §3 — Flujos Funcionales

### F-01: Registro e inicio de sesión
1. El usuario accede a la PWA e ingresa email + contraseña. La pantalla `/login` tiene un toggle entre "Ingresar" y "Registrate" (mismo formulario, cambia el endpoint que llama)
2. El frontend envía las credenciales a FastAPI (`/api/v1/auth/register` o `/login`), que las reenvía a Supabase Auth; Supabase Auth valida/crea el usuario y emite el JWT (access + refresh token) — FastAPI solo retransmite la respuesta, no maneja contraseñas
3. FastAPI crea/asegura la fila correspondiente en `public.users` (email, plan, status) enlazada por `id` a `auth.users`
4. El frontend guarda los tokens en localStorage
5. El usuario es redirigido al chat principal
6. Registro es autoservicio y abierto a cualquier email (sin invitación ni aprobación de administrador) — el rol Administrador (§2) sólo gestiona el corpus de documentos, no usuarios

### F-02: Consulta de chat (RAG)
1. El usuario escribe una consulta (texto) o adjunta una imagen desde cámara/galería
2. El frontend envía la solicitud al backend vía fetch con SSE habilitado
3. FastAPI genera el embedding de la consulta (OpenAI text-embedding-3-small)
4. pgvector realiza búsqueda por similitud coseno y devuelve los 5 chunks más relevantes
5. FastAPI construye el prompt: system + contexto RAG + historial + consulta (+ imagen si aplica)
6. Routing de LLM: si el mensaje es solo texto → Gemini 2.0 Flash; si incluye imagen adjunta → Claude 3.5 Sonnet (visión). El LLM procesa el prompt y devuelve respuesta en streaming
7. FastAPI retransmite el stream al frontend vía SSE y guarda la interacción en Supabase en paralelo
8. La respuesta aparece progresivamente en la interfaz sin citas visibles

### F-03: Gestión de chats
1. El usuario puede iniciar un nuevo chat desde el sidebar
2. El título se genera automáticamente (primera consulta o resumen)
3. El usuario puede renombrar un chat existente desde el menú kebab (⋮) de cada ítem del sidebar
4. El usuario puede eliminar un chat existente desde el mismo menú kebab, con modal de confirmación previo ("¿Eliminar este chat? Esta acción no se puede deshacer"); el menú kebab se cierra automáticamente al hacer clic fuera de él
5. Al eliminar el chat activo: si la vista actual corresponde a ese chat, la pantalla queda en blanco (sin selección); si el usuario está viendo otro chat, permanece sin cambios
6. Eliminar un chat borra en cascada sus mensajes (FK `messages.chat_id → chats.id on delete cascade`)
7. El historial persiste por usuario y es accesible desde cualquier dispositivo

### F-04: Análisis de imagen (multimodal)
1. El usuario adjunta una imagen desde cámara o galería en la interfaz de chat (máx. 5 MB, límite de imágenes base64 de la API de Anthropic)
2. La imagen se sube al bucket privado `chat-attachments` de Supabase Storage, referenciada por su path en `messages.image_url`; en cada lectura del historial se resuelve a una URL firmada de corta duración (no expira el historial, se re-firma en cada fetch)
3. FastAPI arma el mensaje multimodal (imagen base64 + texto + chunks RAG recuperados a partir del texto adjunto, si lo hay) y lo envía a Claude 3.5 Sonnet (visión) en streaming SSE — mismo formato de evento que el chat de texto (Gemini)
4. Claude analiza la imagen combinándola con los chunks RAG recuperados
5. La respuesta integra el análisis visual con el conocimiento del corpus, transmitida progresivamente igual que cualquier otra respuesta del chat

### F-05: Panel de administración de documentos
1. El administrador accede a la ruta protegida `/admin`
2. Puede subir archivos: PDF, Word (.docx), texto plano (.txt), imágenes (.jpg, .png)
3. FastAPI guarda el archivo en Supabase Storage y responde inmediatamente al cliente
4. Un background task procesa el archivo: extracción de texto → chunking → embeddings → pgvector
5. El administrador puede listar documentos (nombre, tipo, estado, cantidad de chunks)
6. El administrador puede eliminar un documento (elimina archivo, chunks y embeddings)
7. El administrador puede crear carpetas y subcarpetas (anidamiento ilimitado) para organizar los documentos subidos, y renombrarlas
8. El administrador puede subir un documento directamente dentro de una carpeta, o mover un documento existente entre carpetas (o a la raíz)
9. La navegación por carpetas se hace desde un árbol lateral (sidebar), estilo file manager clásico: expandir/contraer subcarpetas, ver la carpeta actual resaltada. El listado de la tabla se filtra por la carpeta abierta; buscar por nombre extiende la búsqueda a todo el corpus, no solo a la carpeta actual
10. El administrador puede eliminar una carpeta solo si está vacía (sin documentos ni subcarpetas) — si no lo está, la API devuelve error explícito indicando que debe vaciarse primero (RN-08)
11. El administrador puede reprocesar un documento ya subido sin volver a adjuntarlo: la API re-descarga el archivo original desde Supabase Storage usando el `storage_path` guardado, borra los `document_chunks` existentes de ese documento y vuelve a correr el pipeline completo (extracción → chunking → embeddings → pgvector). Disponible sin importar el estado actual (`processing`, `ready` o `error`) — útil tanto para reintentar un fallo como para re-vectorizar tras un cambio de lógica de ingesta. Acción expuesta como botón "Reprocesar" junto al de eliminar en cada fila de la tabla, con spinner mientras está en curso
12. Cuando el procesamiento de un documento falla (`status = 'error'`), el mensaje de la excepción queda guardado en `error_detail` — el administrador lo ve pasando el mouse (tooltip) sobre el badge "Error" de esa fila, sin depender de revisar logs de Railway para saber qué pasó
13. El botón "Reprocesar" está deshabilitado mientras un documento está en `processing`, salvo que ese intento lleve más de 10 minutos corriendo (comparado contra `processing_started_at`) — en ese caso se habilita, con un tooltip ("Lleva más de 10 minutos procesando"), para permitir reintentar un documento realmente colgado sin esperar indefinidamente
14. El administrador puede descargar el archivo original de un documento ya subido: la API devuelve una URL firmada temporal (mismo patrón que las imágenes del chat, F-04) sin exponer el bucket privado directamente; botón "Descargar" en la tabla, junto a Reprocesar y Eliminar

### F-06: Suscripción con Mercado Pago
1. El usuario en plan gratuito accede al flujo de suscripción
2. Se redirige al checkout de Mercado Pago para suscripción mensual recurrente
3. MP procesa el pago y dispara webhook `subscription.authorized`
4. FastAPI recibe el webhook, valida la firma con `MP_WEBHOOK_SECRET`, y actualiza el estado del usuario a `activo` / plan `pago`
5. El usuario tiene acceso completo de forma inmediata

### F-07: Flujo de mora y reintentos
1. MP rechaza un cobro mensual → webhook `invoice.payment_failed`
2. FastAPI actualiza estado del usuario a `en_mora`
3. La PWA muestra banner persistente invitando a actualizar método de pago
4. El acceso a la IA se degrada al límite del plan gratuito
5. MP reintenta el cobro hasta 4 veces (intervalos automáticos de MP)
6. Si un reintento es exitoso → webhook `invoice.retryed` → FastAPI restaura estado a `activo`
7. Si se agotan los 4 reintentos → MP cancela → webhook `subscription.cancelled` → FastAPI pasa usuario a `cancelado` / plan `gratuito`
8. Para reactivar: el usuario inicia un nuevo flujo de suscripción

### F-08: Instalación PWA
1. En iOS: el usuario accede desde Safari → pantalla de onboarding muestra instrucciones (Safari → Compartir → Agregar a pantalla de inicio)
2. En Android/Chrome: banner nativo de instalación
3. La app queda instalada como ícono nativo con pantalla completa (fullscreen manifest)
4. Service worker permite funcionamiento offline básico (UI cargada, mensajes de "sin conexión" para el chat)

---

## §4 — Modelo de Datos

### Tablas principales (Supabase PostgreSQL)

**users**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | uuid PK | Identificador único (Supabase Auth) |
| email | text unique | Email del usuario |
| plan | enum | `gratuito` \| `pago` |
| status | enum | `activo` \| `en_mora` \| `gratuito` \| `cancelado` |
| mp_subscription_id | text nullable | ID de suscripción en Mercado Pago |
| mp_customer_id | text nullable | ID de cliente en Mercado Pago |
| created_at | timestamptz | Fecha de registro |
| updated_at | timestamptz | Última actualización |

**chats**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | uuid PK | Identificador único del chat |
| user_id | uuid FK → users | Dueño del chat |
| title | text | Título editable (generado automáticamente) |
| created_at | timestamptz | Fecha de creación |
| updated_at | timestamptz | Última actividad |

**messages**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | uuid PK | Identificador único del mensaje |
| chat_id | uuid FK → chats | Chat al que pertenece |
| role | enum | `user` \| `assistant` |
| content | text | Contenido del mensaje |
| image_url | text nullable | URL de imagen adjunta en Supabase Storage |
| created_at | timestamptz | Timestamp del mensaje |

**document_folders**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | uuid PK | Identificador único de la carpeta |
| name | text | Nombre de la carpeta |
| parent_id | uuid FK → document_folders, nullable | Carpeta padre (null = carpeta de nivel raíz) — anidamiento ilimitado |
| created_at | timestamptz | Fecha de creación |
| updated_at | timestamptz | Última actualización (renombre, etc.) |

**documents**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | uuid PK | Identificador único del documento |
| name | text | Nombre del archivo |
| type | enum | `pdf` \| `docx` \| `txt` \| `image` |
| storage_path | text | Ruta en Supabase Storage |
| status | enum | `processing` \| `ready` \| `error` |
| chunk_count | integer | Cantidad de chunks generados |
| folder_id | uuid FK → document_folders, nullable | Carpeta contenedora (null = raíz del corpus) |
| error_detail | text, nullable | Mensaje de la excepción cuando `status = 'error'`; se limpia a null en cada reprocesamiento (exitoso o no, se sobreescribe con el detalle nuevo) |
| processing_started_at | timestamptz, nullable | Momento en que arrancó el intento de procesamiento actual (subida o reprocesamiento); permite distinguir un documento realmente colgado en `processing` de uno que arrancó hace instantes (RN-06) |
| created_at | timestamptz | Fecha de subida |

**document_chunks**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | uuid PK | Identificador único del chunk |
| document_id | uuid FK → documents | Documento origen |
| content | text | Texto del chunk |
| embedding | vector(1536) | Embedding generado por OpenAI |
| chunk_index | integer | Posición del chunk en el documento |
| metadata | jsonb | Página, sección u otros metadatos |

**subscriptions**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | uuid PK | Identificador interno |
| user_id | uuid FK → users | Usuario suscriptor |
| mp_subscription_id | text | ID en Mercado Pago |
| status | enum | `authorized` \| `paused` \| `cancelled` |
| next_payment_date | date | Próximo intento de cobro |
| last_event | text | Último evento de webhook recibido |
| created_at | timestamptz | Fecha de alta |
| updated_at | timestamptz | Última actualización |

### Índices
- `document_chunks.embedding`: IVFFlat (pgvector) — búsqueda por similitud coseno
- `messages.chat_id`: B-tree — paginación de historial
- `chats.user_id`: B-tree — listado de chats por usuario

---

## §5 — Arquitectura Técnica

### Servicios (Railway — mismo proyecto, mismo dashboard)

| Servicio | Tecnología | Responsabilidad |
|----------|------------|-----------------|
| `flippy-web` | Next.js 14 (App Router) + TypeScript | UI PWA, service worker, manifest |
| `flippy-api` | FastAPI (Python 3.11+) | Auth, chat RAG, ingesta, webhooks MP, streaming SSE |

### Stack completo

| Categoría | Tecnología | Versión |
|-----------|------------|---------|
| Framework frontend | Next.js App Router | 14.x |
| Lenguaje frontend | TypeScript | 5.x |
| Framework backend | FastAPI | Python 3.11+ |
| Hosting | Railway (2 servicios) | Starter → Pro según tráfico |
| Base de datos | Supabase PostgreSQL + pgvector | Pro recomendado |
| Storage | Supabase Storage | Incluido en plan |
| Auth | Supabase Auth (GoTrue) | Incluido en plan — email/password, sin confirmación de email en esta fase |
| IA — chat RAG | Google Gemini 2.0 Flash | API (pago por token) |
| IA — análisis de imágenes | Anthropic Claude 3.5 Sonnet | API (pago por token, multimodal) |
| IA — embeddings | OpenAI text-embedding-3-small | API (pago por token) |
| Orquestación RAG | LangChain (Python) | 0.x (pip) |
| Parseo PDF | pdfplumber | pip |
| Parseo Word | python-docx | pip |
| Streaming | Server-Sent Events (SSE) | Nativo FastAPI |
| Pagos | Mercado Pago | API suscripciones recurrentes |
| Control de versiones | GitHub | 2 repos privados: flippy-web + flippy-api |

### Comunicación frontend → backend

```
Base URL:       https://api-flippy.botizar.com/api/v1
Autenticación:  Authorization: Bearer <JWT>
Content-Type:   application/json
Streaming chat: ReadableStream del body de fetch (SSE)
Multi-tenancy:  No aplica — sin headers de tenant ni API key estática
```

El frontend usa `services/api.ts` como único punto de llamadas al backend. Sin axios — fetch nativo del navegador.

### Pipeline RAG

**Ingesta (background task en FastAPI):**
1. Guardar archivo en Supabase Storage
2. Extraer texto: pdfplumber (PDF) / python-docx (Word) / directo (txt) / omitir vectorización (imágenes)
3. Chunking: 500 tokens, overlap 50 tokens, corte inteligente por párrafo
4. Embedding: OpenAI text-embedding-3-small → vector(1536)
5. Indexar en `document_chunks` con IVFFlat en pgvector

**Consulta:**
1. Embedding de la query (OpenAI)
2. Búsqueda coseno en pgvector → top 5 chunks
3. Construcción del prompt:

```
SYSTEM: Eres Flippy, asistente de la comunidad inmobiliaria de [cliente].
        Responde ÚNICAMENTE basándote en el contexto provisto.
        No menciones las fuentes.
        Si no encontrás la respuesta en el contexto, decilo claramente.

CONTEXT: [chunks recuperados de pgvector]
HISTORY: [últimos N mensajes del chat activo]
USER:    [consulta del usuario + imagen si aplica]
```

4. Routing de LLM: solo texto → Gemini 2.0 Flash · con imagen adjunta → Claude 3.5 Sonnet (visión)
5. Streaming SSE del LLM → FastAPI → frontend
6. Guardado en Supabase en paralelo al streaming

### Costos operativos estimados (mensual)

| Servicio | Costo | Notas |
|----------|-------|-------|
| Railway (frontend) | USD 5–10 | Servicio Next.js |
| Railway (backend) | USD 5–15 | Servicio FastAPI |
| Supabase | USD 0–25 | Free hasta 500MB DB; Pro desde USD 25 |
| Google (Gemini 2.0 Flash) | ~USD 0.001/msg | Chat RAG — costo variable principal según volumen |
| Anthropic (Claude) | ~USD 0.003/msg | Solo mensajes con imagen adjunta |
| OpenAI (embeddings) | < USD 1 | Solo al subir documentos |
| Mercado Pago | % por transacción | Sin costo fijo |
| **Total base** | **USD 15–55/mes** | Sin costos de IA variables |

---

## §6 — Reglas de Negocio

### RN-01: Estados de usuario y acceso a IA

| Estado | Descripción | Acceso |
|--------|-------------|--------|
| `activo` | Suscripción vigente y al día | Completo |
| `en_mora` | Pago rechazado, reintentos en curso | Degradado al límite del plan gratuito |
| `gratuito` | Plan gratuito o sin suscripción | Completo durante los primeros 6 meses desde el alta; bloqueado al vencer (ver RN-07) |
| `cancelado` | Suscripción cancelada definitivamente | Solo plan gratuito (sujeto también a la ventana de 6 meses de RN-07) |

### RN-02: Transiciones de estado
Las transiciones de estado **solo** se disparan por webhooks de Mercado Pago, nunca manualmente desde el frontend.

| Evento MP | Transición |
|-----------|------------|
| `subscription.authorized` | → `activo` / plan `pago` |
| `invoice.paid` | Confirma renovación — sin cambio de estado |
| `invoice.payment_failed` | → `en_mora`, acceso restringido, banner activo |
| `invoice.retryed` (exitoso) | → `activo`, banner removido |
| `subscription.cancelled` | → `cancelado` / plan `gratuito` |

### RN-03: Mora y reintentos
- MP realiza hasta 4 reintentos automáticos al fallar un cobro
- Durante mora: banner persistente en la PWA, acceso degradado al nivel gratuito
- Al agotar reintentos: usuario pasa a `cancelado`
- Para reactivar: el usuario debe iniciar un nuevo flujo de suscripción (no se reactiva automáticamente)

### RN-04: Respuestas ancladas al corpus
- Flippy responde **únicamente** basándose en los chunks recuperados del corpus
- Si no hay información suficiente en el contexto, Flippy lo indica explícitamente
- No se muestran referencias a documentos fuente en la interfaz del usuario

### RN-05: Imágenes del corpus vs. imágenes del usuario
- Las imágenes del **corpus** (subidas por el admin) se almacenan en Storage y Claude las procesa en tiempo de consulta — no se vectorizan
- Las imágenes del **usuario** se adjuntan al mensaje y se incluyen en el prompt multimodal junto con los chunks RAG

### RN-06: Administración de documentos
- Solo el administrador puede subir, listar, eliminar o reprocesar documentos del corpus
- Al eliminar un documento se eliminan también sus chunks y embeddings
- El procesamiento es asincrónico — el admin recibe confirmación inmediata y el documento queda en estado `processing` hasta completar la ingesta
- Reprocesar un documento borra sus `document_chunks` existentes antes de regenerarlos — evita duplicados y resultados de búsqueda inconsistentes durante la ventana de re-ingesta (mismo comportamiento asincrónico: el documento vuelve a `processing` hasta completar)
- Si el procesamiento (inicial o reprocesamiento) falla, el mensaje de la excepción se guarda en `documents.error_detail` — se limpia a `null` al iniciar cada nuevo intento y se vuelve a completar solo si ese intento también falla

### RN-07: Vencimiento del plan gratuito (OD-01 resuelta)
- El plan gratuito otorga acceso completo a la IA durante los primeros 6 meses desde la fecha de alta (`users.created_at`)
- Cumplidos los 6 meses sin que el usuario haya iniciado una suscripción paga, el acceso a la IA se bloquea por completo — debe iniciar el flujo de suscripción (F-06) para recuperarlo
- A diferencia de las transiciones de RN-02, este vencimiento es por tiempo, no por webhook de MP — requiere un chequeo programado (job/cron, o verificación en el momento de la consulta comparando `created_at` contra la fecha actual) que identifique usuarios en `gratuito` cuya ventana de 6 meses expiró
- No agrega un campo nuevo a `users` — se calcula a partir de `created_at` (§4) ya existente

### RN-08: Carpetas y subcarpetas de documentos
- Solo el administrador puede crear, renombrar, eliminar o mover carpetas — mismo alcance de rol que RN-06
- Anidamiento ilimitado vía `parent_id` (una carpeta puede contener subcarpetas sin límite de profundidad)
- Una carpeta no puede eliminarse si tiene documentos o subcarpetas — la API rechaza el borrado con un error explícito; el admin debe vaciarla primero (mover o eliminar su contenido)
- Las carpetas son puramente organizativas: no afectan el pipeline de ingesta ni el RAG — chunking, embeddings y retrieval funcionan igual sin importar en qué carpeta esté un documento (o si está en la raíz)

---

## §7 — Integraciones y APIs

### Google Gemini 2.0 Flash
- **Uso:** Generación de respuestas RAG (chat conversacional)
- **Modo:** Streaming vía Google Generative AI SDK (Python), retransmitido por FastAPI como SSE
- **Credencial:** `GOOGLE_API_KEY` solo en `flippy-api`, nunca expuesta al cliente
- **Integración LangChain:** `langchain-google-genai`

### Anthropic Claude (visión)
- **Uso:** Análisis de imágenes adjuntas por el usuario (multimodal / visión)
- **Modelo:** `claude-sonnet-5` — **desviación de este documento**, que especifica "Claude 3.5 Sonnet" (`claude-3-5-sonnet-20241022`, oct-2024, retirado). Verificado en vivo el 2026-07-18 (Incremento 9.2): modelo válido, soporta imágenes, streaming SSE confirmado contra la API real
- **Modo:** wrapper httpx delgado (Python), streaming SSE — consistente con `gemini.py` y con la regla de producto de CLAUDE.md ("streaming en todas las respuestas del chat"); no LangChain
- **System prompt:** propio (`VISION_SYSTEM_PROMPT`, distinto del `SYSTEM_PROMPT` del chat de texto) — el prompt RAG de texto instruye a responder únicamente desde el contexto del corpus, lo que hacía que Claude se negara a analizar la imagen sin contexto relacionado (bug encontrado y corregido en el Incremento 9.2)
- **Credencial:** `ANTHROPIC_API_KEY` solo en `flippy-api`, nunca expuesta al cliente

### OpenAI text-embedding-3-small
- **Uso:** Vectorización de chunks en ingesta y de queries en tiempo de consulta
- **Dimensiones:** 1536
- **Credencial:** API key solo en `flippy-api`
- **Costo:** < USD 1/mes (solo al subir documentos)

### Supabase
- **PostgreSQL + pgvector:** almacenamiento principal + búsqueda vectorial
- **Storage:** archivos originales (PDF, Word, imágenes, texto) y adjuntos de usuario
- **Auth (GoTrue):** registro/login/refresh de usuarios (F-01). FastAPI actúa como proxy hacia `{SUPABASE_URL}/auth/v1/*` — nunca almacena ni hashea contraseñas
- **Validación de sesión:** FastAPI valida los JWT emitidos por Supabase Auth contra el JWKS público del proyecto (`{SUPABASE_URL}/auth/v1/.well-known/jwks.json`, algoritmo ES256) — no depende de ningún secreto compartido
- **Rol administrador:** determinado por lista `ADMIN_EMAILS` (variable de entorno en `flippy-api`), no por tabla de roles
- **Credencial:** `SUPABASE_SERVICE_ROLE_KEY` solo en `flippy-api`, nunca en el frontend

### Mercado Pago
- **Uso:** Suscripciones recurrentes mensuales + webhooks transaccionales
- **Endpoint webhook:** `POST /api/v1/webhooks/mercadopago`
- **Validación:** Firma HMAC con `MP_WEBHOOK_SECRET` antes de procesar cualquier evento
- **Prerequisito cliente:** Módulo de suscripciones recurrentes habilitado en cuenta MP

### Railway
- **Hosting:** `flippy-web` (Next.js) y `flippy-api` (FastAPI) en el mismo proyecto
- **Deploy:** Continuo desde GitHub (push a main → deploy automático), SSL automático
- **Nota:** Sin Vercel — timeouts de serverless incompatibles con procesamiento de documentos

### GitHub
- **Repos:** 2 repositorios privados del cliente: `flippy-web` y `flippy-api`
- **Acceso:** Desarrollador como colaborador (sin compartir contraseñas)

---

## §8 — Estrategia de Testing

### Backend — pytest (flippy-api)
Flujos críticos a cubrir:
- Auth: registro, login, refresh de token, rutas protegidas
- Chat RAG: generación de embedding, recuperación de chunks, construcción de prompt, streaming SSE
- Routing de LLM: mensaje solo texto → Gemini 2.0 Flash · mensaje con imagen → Claude 3.5 Sonnet
- Webhooks MP: validación de firma HMAC, transiciones de estado por evento
- Ingesta: procesamiento de PDF, Word, txt; generación de chunks y embeddings
- Control de planes: acceso restringido en plan gratuito y en_mora

### Frontend — Jest + Playwright (flippy-web)
- **Jest:** componentes críticos (chat input, sidebar, banner de mora, onboarding iOS)
- **Playwright:** flujos E2E (login → chat → historial → cierre de sesión)

### Tests manuales en dispositivo (obligatorio por hito)
- iPhone físico (iOS, Safari) — instalación PWA, flujo completo
- Android físico (Chrome) — instalación PWA, flujo completo
- Chrome desktop — flujo completo

### Sandbox de pagos (Hito 3)
- Flujo de suscripción en sandbox MP
- Pago rechazado → mora → reintento exitoso → restauración
- Agotamiento de reintentos → cancelación

---

## §9 — Seguridad y Compliance (Tier 2 Business)

### Autenticación y autorización
- JWT emitido por FastAPI en login, guardado en localStorage del cliente
- Access token + refresh token — renovación automática antes de expirar
- Rutas de administración protegidas por middleware de autenticación + validación de rol en FastAPI
- Las transiciones de estado de usuario solo se ejecutan desde el backend vía webhooks

### Gestión de secretos
- `SUPABASE_SERVICE_ROLE_KEY`: solo en `flippy-api` como variable de entorno en Railway — nunca en el frontend ni en el repositorio
- `ANTHROPIC_API_KEY`: solo en `flippy-api`
- `GOOGLE_API_KEY`: solo en `flippy-api`
- `OPENAI_API_KEY`: solo en `flippy-api`
- `MP_WEBHOOK_SECRET`: solo en `flippy-api`
- El frontend no tiene credenciales de servicio — solo JWT de usuario

### Webhooks
- Todos los webhooks de MP se validan con firma HMAC (`MP_WEBHOOK_SECRET`) antes de procesar
- Payloads sin firma válida: rechazados con 401 sin procesar

### PII (Tier 2)
- Datos recopilados: email del usuario (obligatorio para registro)
- No se recopilan nombre, teléfono ni dirección
- IDs de Mercado Pago almacenados como referencia opaca
- Política de retención: ver §12 OD-02

### Logging de auditoría (Tier 2 — requisito DoD)
- Eventos a loguear: login/logout, cambios de estado de usuario (con webhook disparador), subida/eliminación de documentos, errores de autenticación
- Los logs no contienen contraseñas, tokens ni contenido de mensajes de usuario

### Errores al cliente
- El backend nunca expone stack traces ni mensajes de error internos
- Respuestas de error: código HTTP + mensaje genérico

---

## §10 — Definition of Done

Un incremento está completo cuando:

**Funcional**
- [ ] El flujo funciona end-to-end según la descripción en §3
- [ ] Probado en dispositivo real (iPhone, Android, Chrome desktop) si aplica al hito

**Tests**
- [ ] Tests automatizados escritos y pasando (pytest / Jest / Playwright según capa)
- [ ] Cobertura en los flujos críticos del incremento

**Seguridad (Tier 2)**
- [ ] Logging de auditoría presente para el evento del incremento
- [ ] Manejo de PII documentado si el incremento toca datos de usuario
- [ ] Errores sanitizados al cliente (sin stack traces expuestos)
- [ ] Auth/autorización revisada si el incremento agrega rutas

**Calidad**
- [ ] Sin credenciales hardcodeadas en el código
- [ ] Variables de entorno documentadas en `.env.example` del servicio correspondiente
- [ ] SPEC.md §13 actualizado

**Documentación**
- [ ] DECISIONS.md actualizado con la decisión principal del incremento

---

## §11 — Fuera de Alcance (v2.0)

- **Micrófono / voz:** fase 2
- **Modo oscuro:** fase 2
- **Multi-tenancy:** Flippy es single-tenant (un cliente, un corpus, una comunidad)
- **Citas visibles:** el RAG opera internamente, nunca muestra referencias al usuario
- **Búsqueda web:** solo corpus interno, no Internet
- **Notificaciones push:** fase 2
- **Panel de analytics:** fase 2
- **Exportar conversaciones:** fase 2
- **SSO / OAuth social:** solo email + contraseña en esta fase

---

## §12 — Decisiones Abiertas

| # | Decisión | Responsable | Estado |
|---|----------|-------------|--------|
| OD-01 | **Límite del plan gratuito:** ¿mensajes/día, mensajes/mes, o acceso a corpus reducido? | Virgilio (cliente) | ✅ Resuelta 2026-07-23 — límite temporal de 6 meses desde el alta, bloqueo total al vencer (ver RN-07) |
| OD-02 | **Política de retención de PII:** ¿cuánto tiempo se conservan los datos de usuarios cancelados? | Virgilio + desarrollador | Pendiente para producción |
| OD-03 | **Cancelado tras haber pagado:** un usuario que sí llegó a pagar y luego cancela (RN-03) hoy conserva "acceso solo plan gratuito" — ¿queda sujeto a la ventana original de 6 meses desde su alta (probablemente ya vencida), o recibe una ventana nueva de 6 meses desde la cancelación? | Virgilio (cliente) | Pendiente de confirmación — bloquea el diseño final de F-06/F-07 |

---

## §13 — AI Authorship Log

| Incremento | Feature | Modelo | Fecha | Notas |
|------------|---------|--------|-------|-------|
| $spec | Spec inicial completa | claude-sonnet-4-6 | 2026-06-30 | Generada desde Flippy_Documento_Proyecto_v2.pdf + CLAUDE.md del proyecto |
| $spec update | Cambio de LLM chat RAG: Claude → Gemini 2.0 Flash | claude-sonnet-4-6 | 2026-07-05 | Claude 3.5 Sonnet queda exclusivamente para análisis de imágenes |
| $spec review | Split LLM propagado a §3, §5, §8, §9 (consistencia) | claude-fable-5 | 2026-07-05 | Routing texto/imagen, costos Gemini, GOOGLE_API_KEY en secretos, test de routing |
| Incremento 1 | Estructura base de servicios (Hito 1) | claude-sonnet-5 | 2026-07-05 | Scaffold FastAPI (flippy-api) + Next.js 14 PWA (flippy-web), health check, manifest/SW, services/api.ts, smoke tests pytest + Jest, ambos verdes |
| Incremento 2 | Modelo de datos — provisioning Supabase (Hito 1) | claude-sonnet-5 | 2026-07-06 | Migraciones SQL para las 6 tablas §4 + índices §4 aplicadas contra Supabase real vía Session Pooler; cliente db.py; 3 tests pytest verdes incluyendo conexión real |
| Incremento 3 | Auth F-01 — Supabase Auth (Hito 1) | claude-sonnet-5 | 2026-07-09 | Registro/login/refresh/me vía Supabase Auth (GoTrue), validación de JWT contra JWKS del proyecto (ES256), rol admin por ADMIN_EMAILS, migración 0004 (FK users→auth.users). Estructura modular (router/services/model) adaptada de examples/main-api del cliente. 6 tests pytest verdes contra Supabase real, con limpieza automática de usuarios de prueba |
| Incremento 3.1 | Fix crítico de seguridad — RLS deshabilitado | claude-sonnet-5 | 2026-07-09 | Supabase reportó alerta crítica: las 6 tablas públicas eran accesibles sin autenticación (rls_disabled_in_public). Migración 0005 habilita Row-Level Security en las 6 tablas — flippy-api sigue funcionando (usa service_role, bypassa RLS); acceso público vía REST bloqueado |
| Incremento 3.2 | Fix estabilidad — leeway en validación JWT | claude-sonnet-5 | 2026-07-09 | Tests intermitentes: ImmatureSignatureError por ~1s de jitter de reloj entre esta VM y Supabase. Agregado leeway=10 en jwt.decode (security.py) — práctica estándar para validar JWT entre sistemas distintos |
| Incremento 4 | UI de chat + sidebar (F-02 layout, F-03) | claude-sonnet-5 | 2026-07-12 | Construida inicialmente sin revisar docs/ a fondo (layout desktop genérico, colores propuestos). Corrección: encontrado brandbook formal + prototipo HTML del cliente en docs/, no revisados hasta este punto — reescritos §C (colores/logo/tipografía explícitos del Manual de Marca Flipping Master) y todos los componentes de chat para ser fieles al prototipo (chathead con estado, chips de sugerencias, burbujas correctas, sidebar con búsqueda/agrupación por fecha/footer). Logo real extraído del prototipo. Responsive: mobile fiel al prototipo (pantallas separadas con toggle), desktop con sidebar persistente (cumple criterio §8 Chrome desktop). 18 tests Jest verdes, build de producción limpio, verificado visualmente con Playwright (screenshots + estilos computados) — detectados y corregidos 2 bugs de CSS (fuentes cayendo a fallback por scope de custom properties; sidebar no ocupando ancho completo en mobile) que no aparecían en los tests |
| Deploy | Primer deploy a Railway (Hito 1) | claude-sonnet-5 | 2026-07-13 | flippy-api y flippy-web deployados como 2 servicios separados desde el mismo repo (Root Directory por servicio), variables de entorno cargadas en Railway, NEXT_PUBLIC_API_BASE_URL de flippy-web apuntando al dominio público de flippy-api. Verificado end-to-end: /api/v1/health responde 200, /chat renderiza correctamente en producción |
| Incremento 5 | Pipeline de ingesta de documentos (F-05 backend, Hito 2) | claude-sonnet-5 | 2026-07-13 | Endpoints admin `/admin/documents` (upload/list/delete) protegidos por `require_admin`; pipeline completo: Supabase Storage → extracción de texto (pdfplumber/python-docx) → chunking por tokens (tiktoken, 500/50 overlap, corte por párrafo) → embeddings OpenAI text-embedding-3-small → pgvector, todo como background task de FastAPI. Imágenes del corpus no se vectorizan (RN-05) — solo se suben y marcan `ready`. Límite de 20MB por archivo. 11 tests pytest verdes contra infraestructura real (Storage + OpenAI + pgvector), incluye caso de documento real procesado end-to-end |
| Incremento 6 | Panel de administración de documentos (F-05 frontend, Hito 2) | claude-sonnet-5 | 2026-07-13 | Login mínimo (`/login`) conectado a Supabase Auth vía flippy-api (primera pieza real de F-01 frontend, hasta ahora pendiente), panel `/admin` con subida/listado/eliminación de documentos, polling automático mientras haya documentos en estado `processing`, redirección a `/login` en 401/403. `services/api.ts` extendido con `apiUpload`/`apiDelete`/`ApiError` tipado. Sin prototipo de referencia del cliente para esta pantalla (el prototipo solo cubre UI de usuario final) — maquetada con los mismos tokens de marca, sin contradecir nada aprobado. 28 tests Jest verdes, build de producción limpio |
| Incremento 6.1 | Fix crítico — CORS faltante bloqueaba todo el frontend | claude-sonnet-5 | 2026-07-13 | El login en producción fallaba: flippy-api no tenía CORSMiddleware configurado, el navegador bloqueaba todos los pedidos de flippy-web hacia flippy-api por política de mismo origen. Agregado CORSMiddleware con origins permitidos (localhost:3000 + WEB_ORIGIN configurable). 2 tests pytest nuevos verificando que el origin de producción es permitido y uno arbitrario no |
| Incremento 6.2 | Refinamiento del panel de administración (F-05 frontend) | claude-sonnet-5 | 2026-07-13/14 | Iteraciones guiadas por el cliente sobre el panel `/admin`: link de acceso desde el sidebar del chat (engranaje), aviso de nombre de archivo duplicado antes de subir, soporte de `.json`/`.html` en la ingesta (migración 0006, extracción con BeautifulSoup para HTML), layout de dos paneles con navbar propio (`AdminSidebar`), tabla a ancho completo con buscador por nombre y paginación 10/50/100, botón de selección de archivo estilizado reemplazando el input nativo |
| Incremento 7 | Chat RAG real — F-02 (Hito 2) | claude-sonnet-5 | 2026-07-14 | Reemplazado el mock de `ChatWindow`/`chat/page.tsx` por el flujo real: módulo `app/modules/chat` (chats/mensajes con ownership por usuario, título autogenerado desde el primer mensaje), embedding de la consulta (OpenAI) + búsqueda coseno en `document_chunks` (top 5), prompt RAG (system + contexto + historial últimos 10 mensajes) enviado a Gemini con streaming SSE real (`app/integrations/gemini.py`, wrapper httpx delgado consistente con el patrón ya usado). Frontend: `ChatWindow` consume el stream vía `apiStream` y renderiza la respuesta progresivamente; `chat/page.tsx` reemplaza `mockChatData` por `/api/v1/chats` real (auto-crea el primer chat, nombre de usuario desde `/auth/me`). Análisis de imagen (F-04) queda explícitamente fuera de este incremento — el input muestra un aviso si se adjunta imagen. **Desviación de SPEC.md §7/§5:** el modelo `gemini-2.0-flash` indicado en el documento fue descontinuado por Google (404 `NOT_FOUND` al probarlo en vivo) — se usa `gemini-2.5-flash` (Flash GA vigente), documentado en DECISIONS.md. Verificado end-to-end contra infraestructura real (Supabase + OpenAI + Gemini con billing habilitado): login, creación de chat, streaming de respuesta y persistencia confirmados por fuera de los tests automatizados. 17 tests pytest y 34 tests Jest verdes, build de producción limpio |
| Incremento 8 | Eliminar y renombrar chat — F-03 (Hito 2) | claude-sonnet-5 | 2026-07-16 | El usuario reportó no poder eliminar un chat; investigación (systematic-debugging) confirmó que el ícono kebab (⋮) del sidebar era decorativo y que ni renombrar ni eliminar tenían endpoint de backend. Agregado backend: `PATCH /api/v1/chats/{id}` (renombrar, valida ownership) y `DELETE /api/v1/chats/{id}` (elimina chat, `messages` cae en cascada por FK existente). Frontend: `ChatSidebar` con menú contextual funcional (Renombrar → input inline; Eliminar → modal de confirmación "no se puede deshacer"), `apiPatch` agregado a `services/api.ts`, `chat/page.tsx` maneja rename/delete optimista y deja la vista en blanco solo si se elimina el chat activo. 5 tests pytest nuevos (rename/delete propio y ajeno, cascada de mensajes, requiere auth) y 3 tests Jest nuevos, ambos suites completas en verde |
| Incremento 8.1 | Fix — menú kebab no se cerraba al hacer clic afuera | claude-sonnet-5 | 2026-07-16 | El usuario reportó que el popup de opciones del chat quedaba abierto al hacer clic en otro lugar. Causa raíz: el menú desplegable solo se cerraba al volver a tocar el mismo kebab o al elegir una opción — nunca tuvo listener de clic externo. Agregado `useEffect` con listener `mousedown` a nivel `document` que cierra el menú cuando el clic ocurre fuera del `<li data-menu-id>` correspondiente. 1 test Jest nuevo (38/38 total en verde) |
| Incremento 9 | Análisis de imagen — F-04 (Hito 2) | claude-sonnet-5 | 2026-07-17 | Cierre del gap detectado en el Incremento 7 (imagen bloqueada con placeholder). Backend: `app/integrations/anthropic_vision.py` (wrapper httpx delgado sobre la Messages API de Claude 3.5 Sonnet, streaming SSE, mismo patrón que `gemini.py`); `supabase_storage.py` generalizado con parámetro `bucket` + `create_signed_url()` (bucket privado nuevo `chat-attachments`, `messages.image_url` guarda el path y se resuelve a URL firmada en cada lectura del historial — así el historial no se rompe cuando la firma expira); nuevo endpoint `POST /{chat_id}/messages/image` (multipart, límite 5 MB — límite real de imágenes base64 de Anthropic) que arma el prompt multimodal (imagen + texto + chunks RAG del texto adjunto) y transmite la respuesta en streaming, igual formato de evento que el chat de texto. Frontend: `apiStreamUpload` en `services/api.ts`; `ChatWindow.tsx` reemplaza el placeholder de F-04 por el flujo real, reutilizando el parser de SSE ya existente (`consumeStream` extraído). **Desviación de SPEC.md §7 (documentada):** el documento original especifica "llamada estándar" (no streaming) para Claude visión; se implementó con streaming para cumplir la regla de producto de CLAUDE.md ("Streaming en todas las respuestas del chat") y mantener consistencia con el chat de texto. **Pendiente de verificación E2E real:** `ANTHROPIC_API_KEY` no está configurada en el entorno (requisito del cliente aún no completado) — los 5 tests pytest nuevos mockean `anthropic_vision.stream_vision` (mismo patrón ya usado para Gemini); la subida a Storage y la resolución de URL firmada sí corren contra Supabase real. 5 tests pytest nuevos (27/27 total) y 2 tests Jest nuevos (39/39 total) verdes, build de producción limpio |
| Incremento 9.1 | Fix proactivo — modelo Claude desactualizado (`claude-3-5-sonnet-20241022` → `claude-sonnet-5`) | claude-sonnet-5 | 2026-07-17 | Verificación post-incremento (WebSearch): el id de modelo especificado en SPEC.md §7 (`claude-3-5-sonnet-20241022`, oct-2024) es casi seguro que está retirado — el lineup vigente confirmado es Fable 5 / Opus 4.8 / Sonnet 5 / Haiku 4.5. Mismo problema que `gemini-2.0-flash` en el Incremento 7, corregido proactivamente en vez de esperar a que falle en producción cuando el cliente configure `ANTHROPIC_API_KEY`. **Sin verificación en vivo** (no hay key configurada) — el cambio se basa en evidencia fuerte (WebSearch + roster de modelos del propio contexto de sesión), no en una confirmación directa contra la API como sí ocurrió con Gemini. Requiere reconfirmar apenas el cliente complete el requisito de cuenta Anthropic |
| Incremento 9.2 | Verificación E2E real de F-04 + fix de bug encontrado (prompt RAG bloqueaba el análisis de imagen) | claude-sonnet-5 | 2026-07-18 | El cliente configuró `ANTHROPIC_API_KEY`. Verificación en vivo: `claude-sonnet-5` confirmado como modelo válido y con soporte de visión (Incremento 9.1 confirmado correcto), formato de streaming SSE parseado correctamente contra la respuesta real de la API. **Bug encontrado y corregido:** el endpoint de imagen reutilizaba `SYSTEM_PROMPT` (el del chat de texto RAG, "Respondé ÚNICAMENTE basándote en el contexto provisto"), causando que Claude se negara a describir imágenes sin contexto de corpus relacionado — el comportamiento opuesto al pedido en F-04 ("Claude analiza la imagen combinándola con los chunks RAG"). Agregado `VISION_SYSTEM_PROMPT` separado en `chat/services.py` que instruye a Claude a analizar la imagen siempre, integrando contexto del corpus solo si es relevante. Verificado en vivo con imagen real (patrón de tablero de ajedrez 64×64) tanto con caption como sin caption — en ambos casos Claude describe la imagen correctamente. 27/27 tests pytest siguen en verde tras el cambio de prompt |
| Incremento 10 | PWA — íconos, meta tags iOS, onboarding de instalación (F-08, Hito 1) | claude-sonnet-5 | 2026-07-19 | Cierre de gaps detectados en la auditoría de Hito 1: `manifest.json` referenciaba `/icons/icon-192.png` e `icon-512.png` que no existían (solo había `logo-shield.png`, 207×245, no cuadrado) — instalabilidad de la PWA rota en la práctica. Generados `icon-192.png`, `icon-512.png` y `apple-touch-icon.png` (180×180) con Pillow a partir del logo existente, centrado sobre fondo `#F4F1EC` (color de marca) con padding de zona segura para íconos maskable; `manifest.json` actualizado con `purpose: "any maskable"`. `layout.tsx`: agregados `metadata.icons.apple`, `metadata.appleWebApp` (capable/statusBarStyle/title) y `viewport.themeColor` vía la Metadata API de Next.js — verificado en el HTML generado por `next build` que los meta tags `apple-mobile-web-app-capable`, `apple-touch-icon` y `theme-color` están presentes. Nuevo componente `IOSInstallBanner.tsx`: detecta iOS Safari no instalado (UA + `navigator.standalone`/`matchMedia('(display-mode: standalone)')`) y muestra un banner persistente con las instrucciones de F-08 punto 1 ("Compartir → Agregar a pantalla de inicio"), dismisseable con persistencia en localStorage. 4 tests Jest nuevos (43/43 total) verdes, build de producción limpio. **Fuera de alcance de este incremento** (no es tarea de código): pruebas en dispositivo físico (iPhone/Android reales) — criterio de aceptación que requiere testing manual del desarrollador, no delegable |
| Incremento 11 | Pantalla de registro — F-01 (Hito 1) | claude-sonnet-5 | 2026-07-19 | Gap encontrado mientras se armaba la checklist de pruebas manuales para el desarrollador: la pantalla `/login` solo tenía formulario de login, sin ningún link ni UI para registrarse — el endpoint `POST /api/v1/auth/register` existía en el backend desde el Incremento 3 pero nunca tuvo consumidor en el frontend, así que no había forma de crear una cuenta real desde la app (solo por API directa o dashboard de Supabase). Confirmado contra §2/§3 de SPEC.md que el modelo de producto es autoregistro abierto (no altas por admin) antes de implementar. `login/page.tsx` ahora tiene un toggle Ingresar/Registrate sobre el mismo formulario (mismos campos, cambia el endpoint llamado); mensajes de error diferenciados (401 login = credenciales inválidas, 422 registro = email ya registrado). §3 F-01 actualizado con el paso del toggle y la aclaración de autoregistro abierto. 4 tests Jest nuevos (46/46 total) verdes, build de producción limpio |
| $spec update | OD-01 resuelta: límite del plan gratuito = 6 meses desde el alta, bloqueo total al vencer (RN-07 nueva) | claude-sonnet-5 | 2026-07-23 | Confirmado por Virgilio vía el desarrollador. Sin cambios de código todavía — el enforcement (job/chequeo por `created_at`) queda pendiente para el incremento de Mercado Pago (F-06/F-07). Nueva OD-03 abierta: interacción con `cancelado` de usuarios que sí llegaron a pagar |
| Incremento 12 | Carpetas y subcarpetas de documentos — F-05, §4, RN-08 (Hito 2) | claude-sonnet-5 | 2026-07-24 | Pedido directo del desarrollador para organizar el corpus a medida que crece. Migración 0007: tabla `document_folders` (`parent_id` self-referencing, anidamiento ilimitado, `on delete restrict` — backstop de RN-08 a nivel DB) + `documents.folder_id`; aplicada contra Supabase real. Backend: `FoldersService` (CRUD + regla de no-borrado si no está vacía, verificada explícitamente antes del delete para devolver 409 con mensaje claro en vez de depender del error de FK) y `DocumentsService.move_document`/`list_documents` extendido con filtro por carpeta; nuevos endpoints `/admin/folders` (CRUD) y `PATCH /admin/documents/{id}/folder`; `POST /admin/documents` acepta `folder_id` opcional (multipart form field). Frontend: `AdminFolderPanel.tsx` (breadcrumb navegable + grid de subcarpetas + crear/renombrar/eliminar inline), `AdminDocumentTable` extendido con selector de carpeta por fila (`onMove`, opcional — no rompe usos existentes sin esa prop), `admin/page.tsx` reescrito para manejar navegación por carpeta + toggle "ver todo el corpus sin filtrar". `apiUpload` en `services/api.ts` generalizado para aceptar campos de formulario extra (mismo patrón que `apiStreamUpload`). 6 tests pytest nuevos contra Supabase real (crear/anidar/renombrar/mover/borrar carpeta, bloqueo de borrado no vacío, documento creado y movido entre carpetas — 31/31 total) y 6 tests Jest nuevos (52/52 total, incluye la suite nueva `AdminFolderPanel.test.tsx`), build de producción limpio |
| Incremento 12.1 | Navegación de carpetas rediseñada como árbol lateral (F-05, punto 9) | claude-sonnet-5 | 2026-07-24 | El desarrollador compartió una referencia visual de file manager (sidebar izquierdo, árbol de carpetas expandible, tabla de archivos con columnas nombre/tamaño/fecha/acciones). `AdminFolderPanel.tsx` reescrito de breadcrumb + grid de tarjetas a un árbol vertical recursivo (expandir/contraer por carpeta, auto-expande la cadena de ancestros de la carpeta actual, ítem activo resaltado); `admin/page.tsx` pasa de 2 a 3 columnas de grid (nav admin | árbol de carpetas | contenido), el breadcrumb se reemplaza por el nombre de la carpeta actual como título del panel principal. Paleta de marca sin cambios (vino/marfil/Cormorant Garamond ya aprobados en §C) — se adaptó la estructura del ejemplo, no sus colores lavanda/violeta. 3 tests Jest nuevos/actualizados (53/53 total), build de producción limpio |
| Incremento 12.2 | Top bar dedicado, búsqueda global entre carpetas e íconos SVG (F-05, punto 9) | claude-sonnet-5 | 2026-07-24 | Ajustes finos pedidos por el desarrollador sobre el árbol de carpetas: (1) barra superior fija ("Documentos" + nombre de la carpeta actual) fuera del grid de 3 columnas, en vez de un `<h1>` dentro del panel principal; (2) `admin/page.tsx` pasa a cargar el corpus completo una sola vez (`?all=true`) y filtra por carpeta en el cliente (`useMemo`), en vez de refetchear por carpeta — esto habilita que la búsqueda de `AdminDocumentTable` alcance documentos fuera de la carpeta abierta (nueva prop `searchScope`, activa solo cuando el campo de búsqueda tiene texto, con aviso visible "Buscando en todo el corpus"); se sacó el checkbox "Ver todo el corpus" (redundante una vez que la búsqueda ya cubre ese caso); (3) íconos de carpeta reemplazados de emoji (📁/🏠) a SVG monoline consistentes con el resto de la app (`FolderIcon`/`RootIcon`, stroke `currentColor`). 4 tests Jest nuevos (55/55 total), build de producción limpio |
| Incremento 12.3 | Top bar de /admin igualada a la del chat (F-05, punto 9) | claude-sonnet-5 | 2026-07-25 | El desarrollador pidió que la barra superior de `/admin` fuera visualmente idéntica a la de `/chat` (`ChatHeader`: escudo + "Flippy" + línea de estado con punto verde), no un `<h1>` propio como en el Incremento 12.2 — solo el texto de estado cambia de "Asistente · activo" a "Documentos" (o "Documentos · {carpeta actual}"). Nuevo componente `AdminTopBar.tsx`, mismo layout/CSS que `ChatHeader` sin el botón de historial (no aplica en `/admin`). 2 tests Jest nuevos (57/57 total), build de producción limpio |
| Incremento 12.4 | Fix — top bar de /admin no debe ocupar todo el ancho (F-05, punto 9) | claude-sonnet-5 | 2026-07-25 | El desarrollador mostró una captura de `/chat`: ahí `ChatHeader` vive dentro de `ChatWindow` (la columna central), no arriba de `ChatSidebar` — el Incremento 12.3 había puesto `AdminTopBar` fuera del grid de 3 columnas, cubriendo todo el ancho de la página (nav admin + árbol de carpetas + contenido), a diferencia del patrón real del chat. Corregido: `AdminTopBar` se movió adentro de `<main>` (columna de contenido), arriba de la tabla — mismo patrón que `ChatWindow` (header fijo + área de contenido con scroll propio debajo). `admin/page.tsx` vuelve a un único `.layout` grid de `height:100vh` (se sacó el wrapper `.page` flex del Incremento 12.2 que ya no hacía falta). 57/57 tests Jest siguen en verde (sin tests nuevos — cambio de posicionamiento, no de comportamiento), build de producción limpio |
| Incremento 12.5 | Ajuste — el header de Documentos cubre también el árbol de carpetas (F-05, punto 9) | claude-sonnet-5 | 2026-07-25 | El desarrollador pidió que el header ("Documentos") se extienda por encima del árbol de carpetas además de la tabla — solo el nav de administración (columna izquierda, `AdminSidebar`) queda sin header propio. `admin/page.tsx` reestructurado: el grid externo pasa de 3 a 2 columnas (`280px 1fr` — nav admin | resto), y el "resto" es una columna flex (`rightPane`) con `AdminTopBar` arriba y una fila (`contentRow`) debajo que contiene `AdminFolderPanel` (220px) + `mainPane` (1fr) lado a lado. 57/57 tests Jest siguen en verde (cambio de layout, no de comportamiento), build de producción limpio |
| Incremento 12.6 | Ajuste visual — header sin logo/marca, título más grande; color propio para Carpetas (F-05, punto 9) | claude-sonnet-5 | 2026-07-25 | `AdminTopBar` simplificado: se sacó el escudo del logo y el nombre "Flippy" (que replicaban el header de `/chat`, ya no pedidos) — queda solo "Documentos" como `<h1>` en tamaño mayor (1.75rem, igual al título original del Incremento 12.2) + el nombre de la carpeta actual al lado, separado por "/". `AdminFolderPanel` cambia su fondo de blanco a `--color-surface-alt` (Gris Niebla, el mismo tono que ya usa `AdminSidebar`) para diferenciar visualmente la columna de navegación de carpetas del contenido blanco de la tabla — sin introducir tokens nuevos, ya aprobados en §C. 2 tests Jest actualizados (57/57 total), build de producción limpio |
| Incremento 12.7 | Fix — peso de "Documentos" no coincidía con "Flippy Admin"; Carpetas usa el color del body (F-05, punto 9) | claude-sonnet-5 | 2026-07-25 | Bug real detectado: `.title` de `AdminTopBar` es un `<h1>`, y `globals.css` define `h1, h2, h3 { font-weight: var(--font-weight-bold) }` globalmente — "Documentos" se renderizaba en negrita aunque comparte `var(--font-primary)` con "Flippy Admin" (`AdminSidebar.brandName`, un `<span>` sin ese peso, hereda regular). Mismo tipo de bug que la staleness de modelos ya visto en el proyecto: una regla global heredada sin querer, no una diferencia de familia tipográfica. Fix: `.title` fija `font-weight: var(--font-weight-regular)` explícitamente. Además, `AdminFolderPanel` cambia su fondo de `--color-surface-alt` (Incremento 12.6) a `--color-bg` — el mismo color que usa `body` (y `.mainPane`), pedido explícito del desarrollador para que Carpetas se funda con el fondo general en vez de leerse como un bloque gris aparte. 57/57 tests Jest siguen en verde, build de producción limpio |
| Incremento 12.8 | Ajuste — header de /admin igualado en alto y estilo de título al header del chat (F-05, punto 9) | claude-sonnet-5 | 2026-07-25 | El desarrollador pidió igualar `AdminTopBar` al `ChatHeader` en dos aspectos puntuales: (1) alto del header — `padding` copiado literal de `ChatHeader.module.css` (`16px 15px 13px` en vez de `20px 24px`); (2) tamaño/estilo de "Documentos" igual al de "Flippy" en el chat — `.title` pasa de `1.75rem` a `16px` (el tamaño exacto de `.name` en `ChatHeader.module.css`), mismo `var(--font-primary)` y peso regular ya fijados en el Incremento 12.7. El nombre de la carpeta actual (`.folder`) se redujo proporcionalmente a `var(--font-size-label)` para mantener la jerarquía visual (título más grande, carpeta como dato secundario), mismo patrón que `.status` es más chico que `.name` en `ChatHeader`. Sin tests nuevos (cambio de tamaños/espaciado, no de comportamiento) — 57/57 tests Jest siguen en verde, build de producción limpio |
| Incremento 12.9 | AdminTopBar vuelve a ser una réplica completa de ChatHeader (con logo) — "Documentos" + estado de carpeta (F-05, punto 9) | claude-sonnet-5 | 2026-07-25 | El desarrollador pidió que el header de `/admin` fuera "igual que el header del chat con el ícono incluido" — el Incremento 12.6 había sacado el escudo del logo por pedido explícito anterior, pero ahora el pedido es la estructura completa de `ChatHeader` (escudo + nombre + línea de estado con punto), adaptando el texto: "Flippy" → "Documentos" (nombre), "Asistente · activo" → "Panel de administración" o "Carpeta: {nombre}" cuando hay una carpeta abierta (estado). `AdminTopBar.tsx`/`.module.css` reescritos como réplica 1:1 de `ChatHeader`/`ChatHeader.module.css` (mismas clases `.logo`/`.identity`/`.name`/`.status`/`.dot`, sin el botón de historial que no aplica). 2 tests Jest actualizados al nuevo texto (57/57 total), build de producción limpio |
| Incremento 12.10 | Filas de carpetas rediseñadas como tarjetas con borde, sin línea vertical de conexión (F-05, punto 9) | claude-sonnet-5 | 2026-07-25 | El desarrollador compartió una referencia visual (jerarquía de categorías de producto: filas con borde redondeado, chevron, ícono, nombre, punto de estado a la derecha, indentación por nivel sin línea de conexión vertical). `AdminFolderPanel` rediseñado: cada carpeta (y "Raíz") pasa de una fila plana a una tarjeta con borde (`--color-line`, se resalta en `--color-primary` al hover/activo) y fondo blanco; nuevo punto de estado (verde, `--color-pine`) al final de cada fila; nombres de carpetas de nivel raíz en mayúscula y negrita para jerarquía visual. La indentación por profundidad se corrigió de "padding interno de la tarjeta" (que no achicaba el borde) a `margin-left` en el `<li>` contenedor — así la tarjeta se angosta y se desplaza a la derecha con cada nivel, en vez de solo mover el contenido adentro de una tarjeta de ancho completo; los bordes derechos quedan alineados en todos los niveles, igual que la referencia. Sin línea vertical de conexión en ningún momento — nunca existió en esta implementación. 57/57 tests Jest siguen en verde (cambio visual, no de comportamiento), build de producción limpio |
| Incremento 12.11 | Filas de carpetas simplificadas a solo texto, ícono únicamente en Raíz, línea vertical de guía por nivel (F-05, punto 9) | claude-sonnet-5 | 2026-07-25 | El desarrollador compartió una referencia distinta (nav tipo Cloudflare: "Investigate" con ícono + chevron, "Log Explorer" sin ícono + chevron, "Log search" indentado con línea vertical de guía, "Trace"/"Logpush" sin chevron) y pidió revertir el estilo de tarjeta del Incremento 12.10 a filas de solo texto, con ícono exclusivamente en el ítem raíz y una línea vertical de conexión para los niveles anidados (lo opuesto al pedido "sin línea vertical" del Incremento 12.10 — se prioriza la instrucción más reciente). `AdminFolderPanel` reescrito: se sacaron el borde/fondo de tarjeta, el punto de estado y el ícono de carpeta por fila (`FolderIcon`, ahora sin uso); el chevron se movió al extremo derecho de la fila (antes a la izquierda); la indentación pasa de `margin-left` numérico por profundidad a un `<ul className={styles.subtree}>` anidado con `border-left` — cada nivel de anidamiento dibuja su propio segmento de línea vertical de forma natural por el propio anidamiento del DOM, sin necesidad de calcular la profundidad manualmente (se sacó el parámetro `depth` de `renderNode`). Sin tests nuevos (cambio visual, la lógica de expandir/navegar/renombrar/eliminar no cambió) — 57/57 tests Jest siguen en verde, build de producción limpio |
| Incremento 12.12 | Fix — Raíz contiene visualmente a las carpetas de nivel superior; chevron SVG consistente; se saca la palabra "Carpetas" (F-05, punto 9) | claude-sonnet-5 | 2026-07-26 | Tres ajustes puntuales sobre el árbol de carpetas: (1) "no se nota que la carpeta raíz contiene al resto" — las carpetas de nivel superior ("Valores", "Valores 3", etc.) eran hermanas de "Raíz" en la misma lista, sin línea de guía conectándolas; ahora se anidan dentro del `<li>` de "Raíz" en un `<ul className={styles.subtree}>` (mismo mecanismo que cualquier subcarpeta), heredando la línea vertical y mostrando contención real; (2) el chevron de texto (▾/▸, tamaño y grosor inconsistentes entre estados) se reemplazó por un ícono SVG único que rota 90° al expandir (`ChevronIcon`), mismo ícono y tamaño en ambos estados; (3) se sacó el encabezado "Carpetas" del panel (redundante con el título "Documentos" del header y con el label ARIA del `<nav>`). 57/57 tests Jest siguen en verde (cambio visual/estructural, sin impacto en comportamiento), build de producción limpio |
| Incremento 12.13 | AdminUploadForm rediseñado como barra de ruta estilo GitHub (breadcrumb + botón único de subida) (F-05, punto 9) | claude-sonnet-5 | 2026-07-26 | El desarrollador compartió una captura de un repo de GitHub (`flippy / checks /` a la izquierda, botón "Add file" a la derecha) y pidió eliminar la tarjeta "Subir documento a..." y reemplazarla por ese patrón: a la izquierda, la ruta de la carpeta actual como breadcrumb navegable ("Raíz / Presupuestos / 2026 /", cada segmento salvo el último es un link que navega con `onNavigate`); a la derecha, un único botón "Agregar archivo". Se simplificó el flujo de subida: ya no hay un botón "Elegir archivo" separado de "Subir" — un solo click abre el selector nativo y, apenas se elige un archivo válido (nombre no duplicado), la subida arranca automáticamente (el botón pasa a "Subiendo…" y se deshabilita); si el nombre ya existe, se bloquea y se muestra la advertencia sin subir, igual que antes. `AdminUploadForm` ahora recibe `folders`/`currentFolderId`/`onNavigate` en vez de `currentFolderName` (string plano) para poder construir la cadena de ancestros y hacerla clickeable. Tests reescritos para el nuevo flujo sin botón "Subir" + 1 test nuevo de breadcrumb/navegación (58/58 total), build de producción limpio |
| Incremento 12.14 | Botón de subida renombrado a "Subir archivo" con el mismo estilo que "+ Nueva carpeta" (F-05, punto 9) | claude-sonnet-5 | 2026-07-26 | El desarrollador pidió que el botón "Agregar archivo" (Incremento 12.13, sólido vino) pasara a decir "Subir archivo" y usara el mismo estilo visual que el botón "+ Nueva carpeta" de `AdminFolderPanel` — borde punteado en `--color-primary`, fondo transparente, texto en `--color-primary`, mismo padding/radio. `.addButton` en `AdminUploadForm.module.css` se reescribió con esos mismos valores (antes: fondo sólido `--color-primary`, texto blanco, negrita) para que ambas acciones de "crear/agregar contenido" en el panel de admin compartan un lenguaje visual consistente. Sin tests nuevos (cambio de texto/estilo, no de comportamiento) — 58/58 tests Jest siguen en verde, build de producción limpio |
| Incremento 12.15 | Botón "Subir archivo" con borde sólido; zona de arrastrar-y-soltar estilo GitHub con soporte multiarchivo (F-05, punto 9) | claude-sonnet-5 | 2026-07-26 | El desarrollador compartió una captura de la página "Upload files" de GitHub (zona con ícono de archivo, "Drag files here to add them to your repository", link "choose your files") y pidió dos cosas: (1) que el borde de "Subir archivo" dejara de ser punteado y pasara a sólido, manteniendo el color de "+ Nueva carpeta"; (2) copiar el formato de subida de GitHub, con soporte para múltiples archivos a la vez. Implementado: el botón "Subir archivo" ahora abre/cierra (toggle) una zona de arrastrar-y-soltar debajo de la barra de ruta — ícono de archivo, texto "Arrastrá archivos acá para agregarlos al corpus", y un link "elegí tus archivos" que abre el selector nativo con soporte `multiple`. `handleFiles` recibe una lista de archivos (por drop o por selección), separa los que ya existen en el corpus (bloqueados, con aviso pluralizado) de los válidos, y sube estos últimos secuencialmente mostrando progreso ("Subiendo N de M: nombre.pdf"); si todos suben sin error y no hubo duplicados, el panel se cierra solo. Tests existentes ajustados para abrir el panel primero (`fireEvent.click("Subir archivo")`) + 1 test nuevo de subida múltiple (59/59 total), build de producción limpio |
| Incremento 12.16 | Cola de archivos con tabla y botón "Subir N archivos" — la subida deja de ser automática al seleccionar (F-05, punto 9) | claude-sonnet-5 | 2026-07-26 | Con una nueva captura del flujo real de GitHub (la zona de arrastrar-y-soltar sumada a una tabla de archivos ya agregados, cada uno con su botón "✕" para quitarlo antes de confirmar el commit), el desarrollador pidió explícitamente que la subida dejara de ser automática al elegir/soltar archivos (comportamiento del Incremento 12.15) y pasara a un flujo de cola: los archivos elegidos se agregan a una lista visible (con ícono + nombre + botón de quitar), y solo se suben a la base cuando el usuario confirma con un botón "Subir N archivo(s)" explícito. Se agregó estado `pendingFiles: QueuedFile[]` (cada uno con un `id` único generado a partir de nombre+tamaño+`lastModified`+random, para permitir remover ítems individuales aunque haya nombres repetidos entre selecciones); `addFiles` reemplaza a la vieja `handleFiles` — ya no sube nada, solo valida duplicados (contra `existingNames` y contra los ya encolados) y encola los válidos; nueva `handleUploadQueue` sube la cola completa secuencialmente cuando se hace click en el botón de proceso, saca de la cola los que subieron bien y deja los que fallaron (con el mismo mensaje de error de antes) para reintentar. Tests reescritos: verifican que seleccionar/soltar NO llama a `onUpload` hasta hacer click en "Subir N archivos", que se puede quitar un archivo de la cola antes de subir, y que los duplicados nunca llegan a encolarse (60/60 total), build de producción limpio |
| Incremento 12.17 | La tabla de documentos se oculta mientras el módulo de subida está abierto (F-05, punto 9) | claude-sonnet-5 | 2026-07-26 | El desarrollador señaló que la tabla de documentos quedaba visible debajo de la zona de arrastrar-y-soltar y la cola de archivos, empujada hacia abajo — pidió tratar el módulo de subida como una unidad propia que oculte la tabla mientras está abierto, y que la tabla vuelva a aparecer (ya actualizada) cuando la subida termina. `AdminUploadForm` gana una prop opcional `onPanelOpenChange(isOpen)` que se dispara cada vez que el panel se abre o se cierra (al tocar "Subir archivo", o automáticamente al terminar de subir sin errores); `admin/page.tsx` guarda ese estado en `isUploadPanelOpen` y solo renderiza `AdminDocumentTable` (o el "Cargando documentos…") cuando el panel está cerrado. Como `handleUpload` ya recargaba la lista de documentos después de cada subida exitosa, la tabla aparece con los archivos nuevos apenas se cierra el panel — sin lógica adicional de refresco. Sin tests nuevos (cambio de composición entre componentes, la lógica interna de cada uno no cambió) — 60/60 tests Jest siguen en verde, build de producción limpio |
| Incremento 12.18 | Cerrar la subida vuelve a mostrar la tabla al navegar de carpeta; botón "✕" explícito para cerrar el panel (F-05, punto 9) | claude-sonnet-5 | 2026-07-26 | El desarrollador pidió dos ajustes al módulo de subida (Incremento 12.17): (1) que al hacer click en una carpeta del árbol se vea la tabla de documentos — antes, si el panel de subida quedaba abierto y el usuario navegaba a otra carpeta, la tabla seguía oculta porque `isUploadPanelOpen` no cambiaba solo; (2) dar una forma explícita de cerrar la subida de archivos, más allá de volver a tocar "Subir archivo" (un toggle no obvio). Implementado: nuevo `useEffect` en `AdminUploadForm` con `currentFolderId` como dependencia — cierra el panel y vacía la cola de archivos pendientes cada vez que cambia la carpeta actual (necesario además porque la cola no lleva la carpeta de destino consigo: si el usuario navegaba con archivos en cola y los procesaba después, subirían a la carpeta *nueva*, no a la que estaban destinados — se prioriza evitar esa subida al lugar equivocado sobre preservar la cola entre carpetas). Nuevo encabezado dentro del panel ("Subir archivos" + botón "✕" con `aria-label="Cerrar subida de archivos"`) que cierra el panel explícitamente sin depender del toggle del botón de la barra. 2 tests nuevos: cierre vía el botón "✕", y cierre + vaciado de cola al cambiar `currentFolderId` (62/62 total), build de producción limpio |
| Incremento 13 | Reprocesar documento sin volver a subirlo (F-05, punto 11, RN-06) | claude-sonnet-5 | 2026-08-02 | El desarrollador consultó si un documento ya subido se puede reprocesar; sin esa opción, la única salida era borrarlo y volver a subirlo. Backend: `DocumentsService.prepare_reprocess` re-descarga el archivo original desde Supabase Storage vía `storage_path`, borra los `document_chunks` existentes y marca el documento `processing` antes de encolar `process_document` como background task; nuevo `download_file` en `supabase_storage.py`; endpoint `POST /admin/documents/{id}/reprocess` (`require_admin`). Frontend: botón ↻ junto a "Eliminar" en cada fila de `AdminDocumentTable`, `handleReprocess` en `admin/page.tsx` reutiliza el polling de `processing` ya existente. **QA de seguridad sobre el propio incremento (Security Reviewer) encontró y corrigió, con aprobación explícita del desarrollador:** (1) orden de operaciones invertido — la descarga desde Storage se confirma *antes* de borrar chunks/marcar `processing`, evitando que una descarga fallida deje el documento trabado sin datos; (2) `SupabaseStorageError` ahora se captura en el router y responde 502 sanitizado en vez de propagar un 500 no controlado; (3) sanitización de `name` al construir `storage_path` en `create_document` (nueva `_sanitize_filename`, remueve separadores de ruta y secuencias `..`) — cierra un path traversal preexistente en upload/delete que el nuevo `download_file` también heredaba. 4 tests pytest nuevos incluyendo el caso de sanitización (13/13 en `test_documents.py`) y 1 test Jest nuevo (9/9 en `AdminDocumentTable.test.tsx`), ambas suites completas en verde |
| Incremento 13.1 | Reprocesar — botón de texto con color propio, spinner mientras está en curso, estado en vivo (F-05, punto 11) | claude-sonnet-5 | 2026-08-02 | El desarrollador pidió tres ajustes sobre el botón ↻ del Incremento 13: (1) que fuera un botón de texto "Reprocesar" como "Eliminar", con otro color — pasó de ícono `↻` a texto, usando `--color-primary` (vino de marca) en vez del gris genérico anterior, para diferenciarse visualmente de "Eliminar" (rojo `--color-error`); (2) un spinner mientras el reprocesamiento está en curso; (3) que el estado se refleje al terminar. Implementado: `admin/page.tsx` trackea `reprocessingIds: Set<string>` durante el round-trip del `fetch` (se agrega el id al hacer click, se saca en el `finally`) y actualiza `allDocuments` de forma optimista con el `status`/`chunk_count` que devuelve la respuesta del endpoint (pasa a `processing` de inmediato en vez de esperar al próximo ciclo de polling); el polling ya existente (`hasProcessing` en el `useEffect`) se dispara solo por ese cambio de estado y termina de reflejar `ready`/`error` cuando el background task del backend completa — sin lógica de refresco nueva. `AdminDocumentTable` recibe la nueva prop opcional `reprocessingIds`, deshabilita el botón mientras el id está en ese set o mientras `doc.status === "processing"`, y muestra un spinner CSS (`@keyframes spin`) junto al texto durante el request en curso. 2 tests Jest nuevos (botón deshabilitado durante `processing`, spinner visible durante el request — 11/11 en `AdminDocumentTable.test.tsx`), build de producción limpio |
| Incremento 14 | Detalle de error de ingesta — documents.error_detail (F-05, punto 12; §4; RN-06) | claude-sonnet-5 | 2026-08-02 | El desarrollador pidió investigar por qué el documento `ddcb7017-...` había quedado en `status='error'`; la investigación (reproducción completa del pipeline con el archivo real: descarga, extracción, chunking y embeddings, todos exitosos) concluyó que fue una falla transitoria — pero no había forma de confirmarlo porque `process_document` atrapaba cualquier excepción sin persistir su mensaje, y no había acceso a Railway CLI en este entorno para revisar logs. Migración 0008: nueva columna `documents.error_detail` (text, nullable). `DocumentsService.process_document` ahora guarda `str(exc)[:2000]` en `error_detail` al fallar, y lo limpia (`= null`) en cada camino de éxito; `prepare_reprocess` también lo limpia al reiniciar un intento. `list_documents`/`move_document` lo incluyen en la respuesta; `DocumentResponse` gana el campo opcional `error_detail`. Frontend: el badge "Error" de `AdminDocumentTable` muestra el mensaje como `title` (tooltip nativo) cuando está presente; `handleReprocess` en `admin/page.tsx` propaga `error_detail` en la actualización optimista. 1 test pytest nuevo que fuerza un PDF inválido y verifica que `error_detail` queda poblado (14/14 en `test_documents.py`) y 1 test Jest nuevo (12/12 en `AdminDocumentTable.test.tsx`), ambas suites completas en verde, build de producción limpio |
| Incremento 14.1 | Fix — apply_migrations.py no leía variables de entorno de Railway (500 en producción) | claude-sonnet-5 | 2026-08-03 | El desarrollador reportó CORS bloqueado en `/admin`; investigación (systematic-debugging) descartó service worker/caché (persistía en incógnito) y encontró, vía curl directo contra producción, un 500 real cuyo header CORS falta porque Starlette no lo agrega a excepciones no controladas (el síntoma reportado). El log de runtime de Railway (pedido al desarrollador, sin acceso propio a Railway CLI) mostró la causa exacta: `psycopg2.errors.UndefinedColumn: column "error_detail" does not exist` — la migración 0008 se había aplicado contra la base del `.env` local de este entorno, pero `apply_migrations.py` usaba `dotenv_values()` exclusivamente (solo lee un archivo `.env` literal); Railway inyecta variables de entorno directo al proceso, sin archivo `.env`, así que el script nunca pudo correr ahí (`SUPABASE_DB_URL is not set in .env` al intentarlo desde la Console de Railway) y la base real de producción se quedó sin la columna nueva. Fix: `env = {**os.environ, **dotenv_values(...)}` — prioriza el entorno real del proceso, con el archivo `.env` local como override para desarrollo. El desarrollador corrió el script desde la Console de Railway tras el redeploy; confirmado el 500 resuelto |
| Incremento 14.2 | Fix — extract_text elimina bytes NUL antes de insertar en Postgres (reprocesar seguía fallando) | claude-sonnet-5 | 2026-08-03 | Con `error_detail` ya funcionando en producción (Incremento 14.1 resuelto), el desarrollador reportó que reprocesar el documento seguía dando error — esta vez el propio `error_detail` reveló la causa sin necesidad de logs de Railway: `A string literal cannot contain NUL (0x00) characters.` El PDF real (`FlippingMasters_Proveedores_COMPLETO_al_25-06-2026.pdf.pdf`) tiene bytes `\x00` embebidos en su texto, que pdfplumber preserva y que Postgres rechaza en columnas `text`. Fix en `parsers.py`: `extract_text` centraliza el `text.replace("\x00", "")` para los 5 tipos vectorizables (antes cada `_extract_*` retornaba directo). Verificado localmente contra el archivo real: el texto extraído ya no contiene NUL. 1 test nuevo (`tests/test_parsers.py`, 15/15 total en la suite de documentos+parsers), build limpio |
| Incremento 15 | Reprocesar documentos colgados en processing + tabla de documentos contenida (F-05, punto 13; §4) | claude-sonnet-5 | 2026-08-03 | El desarrollador pidió: (1) habilitar el reproceso de documentos que quedaron en `processing` cuando ese intento lleva más de 10 minutos corriendo; (2) achicar las columnas Estado y Carpeta de la tabla; (3) que la tabla ocupe el 100% del ancho disponible sin expandirse hacia la derecha. Migración 0009: nueva columna `documents.processing_started_at` (timestamptz, nullable; backfill a `created_at` para filas existentes). `create_document` y `prepare_reprocess` la actualizan a `now()` en cada intento nuevo. Frontend: `isStuckProcessing(doc)` en `AdminDocumentTable` compara `Date.now() - processing_started_at` contra 10 minutos; el botón "Reprocesar" se habilita solo en ese caso (con tooltip explicando por qué), en vez de quedar bloqueado mientras `status === 'processing'` sin excepción. Tabla: `<colgroup>` con anchos fijos por columna (`table-layout: fixed`) — Estado 100px, Carpeta 150px (antes auto-dimensionadas por contenido) — envuelta en un `div` con `overflow-x: auto` para que el contenido ancho haga scroll interno en vez de empujar el layout de `/admin` hacia la derecha. 2 tests Jest nuevos (documento colgado hace 11 min habilita el botón con tooltip; documento procesando hace 2 min lo mantiene deshabilitado — 14/14 en `AdminDocumentTable.test.tsx`), build de producción limpio |
| Incremento 16 | Spinner de marca en estados de carga de página completa (Identidad visual) | claude-sonnet-5 | 2026-08-03 | El desarrollador pidió que los estados de carga de página fueran un spinner con el símbolo de Flippy, en vez de texto plano. Nuevo componente reutilizable `LoadingSpinner.tsx`: anillo circular girando (`border-top-color: var(--color-primary)`, vino de marca) con el escudo (`/icons/logo-shield.png`, ya usado en `ChatHeader`) centrado y contra-rotando a la misma velocidad para que se vea estático mientras el anillo gira alrededor. Reemplaza el texto "Cargando…" de `/chat` (`app/chat/page.tsx`) y "Cargando documentos…" de `/admin` (`app/admin/page.tsx`) — únicos dos estados de carga de página completa detectados en el código; el texto de "Ingresando…"/"Creando cuenta…" del botón de `/login` no se tocó por ser feedback de botón, no de página. 3 tests Jest nuevos (`LoadingSpinner.test.tsx`: logo presente, label opcional se muestra/omite — 71/71 total en la suite), build de producción limpio |
| Incremento 17 | Descargar documento original (F-05, punto 14) | claude-sonnet-5 | 2026-08-03 | El desarrollador preguntó si se puede descargar un documento ya subido — no existía esa opción. Backend: `DocumentsService.get_download_url` reutiliza `supabase_storage.create_signed_url` (mismo patrón que las imágenes del chat, F-04) para devolver una URL firmada de corta duración (5 minutos) sin exponer el bucket privado directamente; nuevo endpoint `GET /admin/documents/{id}/download` (`require_admin`), captura `SupabaseStorageError` como 502. Frontend: botón "Descargar" en `AdminDocumentTable`, junto a Reprocesar y Eliminar (columna Acciones ampliada a 330px para las tres); `handleDownload` en `admin/page.tsx` pide la URL y abre `window.open` en pestaña nueva. 3 tests pytest nuevos (URL firmada devuelta, 404 si no existe, requiere admin — 17/17 en `test_documents.py`) y 1 test Jest nuevo (72/72 total), build de producción limpio |
| Incremento 18.1 | Migración 002 (SPEC_RAG.md) — chunking por estrategia + metadatos tipados + HNSW | claude-sonnet-5 | 2026-08-03 | Primer incremento del pipeline RAG de SPEC_RAG.md (ver §A Delta Log #14). Migración `0010_rag_chunking_metadata.sql` aplicada contra Supabase real: enum `chunking_strategy`, columnas `documents.strategy/strategy_source/strategy_reason/token_count/indexed_at`, columnas tipadas en `document_chunks` (`fecha_vigencia`, `tipo`, `moneda`, `region`, `es_primaria`, `header_text`, `token_count`), índices de pre-filtrado, swap de índice vectorial IVFFlat → HNSW guardado con chequeo de `pg_am` para que `apply_migrations.py` no lo reconstruya en cada deploy. Verificado post-aplicación vía consulta directa a `information_schema`/`pg_am` |
| Incremento 18.2 | Router de chunking por estrategia (SPEC_RAG.md §1, §3) | claude-sonnet-5 | 2026-08-04 | `chunking.py` reescrito: enum `ChunkingStrategy`, `Chunk`/`DocumentMeta`, 5 chunkers (`atomic`/`by_section`/`by_topic`/`by_qa_pair`/`fixed_500`) + `infer_strategy()` + router `chunk_document()`. `services.py`/`router.py` persisten `strategy`/`strategy_source`/`strategy_reason`/`token_count`/`indexed_at` por documento. Estrategia siempre inferida por ahora (selector manual pospuesto a un incremento aparte al final, decisión del desarrollador). Detección de encabezados es heurística sobre texto plano (parsers.py no preserva marcado estructural) — limitación conocida, documentada en el módulo. 32 tests nuevos (`test_chunking.py`) cubren los 5 invariantes de §3.3 parametrizados sobre las 5 estrategias; bug de redondeo BPE en el corte de emergencia por tokens crudos encontrado y corregido durante el desarrollo de los tests. Suite completa 72/72, sin regresiones |
| Incremento 18.3 | Extracción de metadatos vía modelo (SPEC_RAG.md §6) | claude-sonnet-5 | 2026-08-04 | Nuevo `metadata.py`: pasada determinística (fecha desde nombre de archivo) + pasada vía modelo (Gemini 2.5 Flash, reutiliza `GOOGLE_API_KEY` ya configurada; nueva `gemini.generate_text()` no-streaming). Vocabulario cerrado de §6.3 normaliza valores fuera de vocabulario a `null` y loguea. `process_document` llama a `extract_metadata()` una vez por documento, propaga los campos a cada `document_chunks`, marca `documents.needs_review` en `confianza: baja`. Migración `0011_documents_needs_review.sql` (columna faltante de la migración 002 original, §6.5). 13 tests nuevos (`test_metadata.py`, Gemini mockeado vía `monkeypatch` salvo en los tests de `test_documents.py` que corren el pipeline completo contra la API real). Suite completa 85/85, sin regresiones |
| Incremento 18.4 | Header enrichment (SPEC_RAG.md §4) | claude-sonnet-5 | 2026-08-04 | `enrich_with_header()` en `chunking.py` — formato exacto de §4.2, campos ausentes omitidos, nunca `Fecha: None`. `process_document` reordenado: `extract_metadata()` ahora corre antes de embeber (antes se llamaba después, sin usarse), propaga metadatos del documento a cada `Chunk`, aplica el header, persiste `header_text`; `content` (usado en el prompt de chat) nunca lo lleva, solo `embeddable_text` (usado para vectorizar). 5 tests nuevos (`test_chunking.py::TestEnrichWithHeader`). Suite completa 90/90, sin regresiones |
| Incremento 18.5 | Recuperación con filtrado por intención (SPEC_RAG.md §7) | claude-sonnet-5 | 2026-08-04 | Nuevo `chat/retrieval.py` reemplaza la consulta plana top-5 sin filtro. Clasificación de intención por keywords (5 intenciones + fallback general), `WHERE tipo = ANY(...)`, umbral de similitud 0.25, `SET LOCAL hnsw.ef_search=100`. Ventana temporal obligatoria para `precio_actual` (6m) y `costo_obra` (4m), ampliación progresiva 12m→24m→sin filtro si <3 chunks, con nota de posible desactualización en el prompt (sin citar fuente). Filtrado por región no implementado — §7.2 no define heurística para derivarla de texto libre, gap documentado. 11 tests nuevos (`test_retrieval.py`). Suite completa 101/101, sin regresiones |
| Incremento 18.6 | Set de evaluación + reprocesamiento del corpus real (SPEC_RAG.md §8) | claude-sonnet-5 | 2026-08-04 | `tests/eval/queries.json` (30 preguntas reales, contenido verificado contra `document_chunks` real) + `scripts/evaluate_rag.py` (4 métricas de §8.4). Corpus real (49 documentos) reprocesado con `scripts/reprocess_all_ready.py` (nuevo) — estaba ingerido con el pipeline viejo, `tipo`/`fecha_vigencia` en NULL. Resultado tras reprocesar: `recall_at_k=0.88`, `mrr=0.72` (objetivo cumplido); `intent_acc=0.17` inicial, muy por debajo del umbral de reevaluación de §7.5 — se amplió `_INTENT_RULES` con variantes reales de fraseo, subiendo a 0.77 pero bajando `recall_at_k` a 0.60 por una interacción real entre el filtro de tipo y el criterio de corte "≥3 resultados" del ensanchamiento temporal de §7.3 (documentada como limitación conocida, no arreglada en este incremento). Pendiente explícito: barrido de calibración de §8.5 (requiere re-embeder el corpus, operación cara, ítem aparte del checklist §10) |
| Incremento 18.7 | Re-ranking blando reemplaza la cascada de filtros duros (desviación de §7.3/§7.4) | claude-sonnet-5 | 2026-08-04 | Diagnóstico del Incremento 18.6 con 3 causas raíz concretas (tipo `faq` fuera del filtro de metodologia, ventana temporal excluye `fecha_vigencia IS NULL` sin nunca ensanchar del todo por el corte "≥3", metadatos de tipo demasiado gruesos por documento). Fix: `retrieval.py` reescrito — candidate pool de 30 solo por similitud, scoring con bonus/penalidad (tipo +0.15, fecha ausente -0.03, dato muy viejo -0.06) en vez de exclusión SQL dura; `faq` sumado al filtro de metodologia; `SIMILARITY_THRESHOLD` 0.25→0.40 con evidencia real; `metadata.py` reconoce meses en español en nombres de archivo (Mar2026, julio_2026). Corpus reprocesado de nuevo. Resultado medido sobre las mismas 30 preguntas: `recall_at_k` 0.60→0.96, `mrr` 0.50→0.78, `refusal_acc` 0.50→1.00 (los 3 ahora sobre objetivo); `intent_acc` sin cambios (0.77, objetivo 0.80 — pendiente, ya no oculta chunks al fallar). Suite completa 111/111, sin regresiones |
| Incremento 19 | Fix — embeddings en lotes para documentos grandes (SPEC.md §5) | claude-sonnet-5 | 2026-08-05 | El desarrollador reportó que "Todo Flippy Remodelador.pdf" daba error al subir. Investigación: `error_detail` (ya persistido desde el Incremento 14) mostró la causa exacta sin necesidad de logs — `openai_embeddings.embed_texts` mandaba TODOS los chunks del documento en un único request a la API de OpenAI; este PDF generó 895.504 tokens en una sola llamada, muy por encima del límite de 300.000 tokens por request. Fix: nueva `DocumentsService._embed_in_batches` acumula chunks hasta un límite de ~250.000 tokens (margen de seguridad) o 500 ítems por lote, llamando a `embed_texts` una vez por lote en vez de una vez por documento. Reprocesado el documento real tras el fix: `status=ready`. 3 tests nuevos (`test_embedding_batching.py`, mockeando `embed_texts` vía monkeypatch — no depende de la API real), 21/21 en la suite de documentos+parsers+batching, sin regresiones |
| Incremento 20 | Spinner al eliminar carpeta + error visible en la grilla de documentos (F-05, RN-08) | claude-sonnet-5 | 2026-08-05 | El desarrollador reportó dos cosas de UX: (1) al eliminar una carpeta no había ninguna señal de que la acción estuviera en curso; (2) el `error_detail` de un documento en estado error solo se veía al pasar el mouse sobre el badge, no directamente en la grilla. Fix (1): `AdminFolderPanel` recibe `deletingIds` (Set), muestra un spinner reemplazando el ícono ✕ y deshabilita renombrar/eliminar mientras la carpeta en cuestión se está borrando; `admin/page.tsx` trackea `deletingFolderIds` igual que ya hacía `reprocessingIds` para documentos. Fix (2): `AdminDocumentTable` renderiza `error_detail` como texto (clamp a 2 líneas, `title` con el texto completo) debajo del nombre del archivo cuando `status === 'error'`, además del tooltip existente en el badge. 3 tests Jest nuevos (spinner de carpeta deshabilita acciones; error visible en la grilla — 74/74 total), build de producción limpio |
| Incremento 21 | Spinner al eliminar un documento (F-05, punto 6) | claude-sonnet-5 | 2026-08-05 | Mismo pedido que el Incremento 20 pero para documentos: `handleDelete` en `admin/page.tsx` dejó de sacar la fila de la tabla de forma optimista al hacer click — ahora agrega el id a `deletingDocumentIds`, el botón "Eliminar" muestra un spinner (variante en rojo, `.spinnerError`, consistente con el color del botón) y queda deshabilitado mientras dura el request, y la fila recién se saca de la lista cuando el backend confirma el borrado. Si falla, la fila permanece (antes desaparecía igual y solo se restauraba tras un `loadDocuments()` de respaldo). 2 tests Jest nuevos (aria-label en el botón Eliminar para queries precisas + spinner/disabled durante el borrado — 75/75 total), build de producción limpio |
| Incremento 22 | Fix — modelo Gemini desactualizado tras rotación de API keys (§5, §7) | claude-sonnet-5 | 2026-08-06 | El desarrollador rotó las tres API keys (Google/OpenAI/Anthropic) en Railway y reportó que el chat dejó de responder ("No pudimos generar una respuesta. Intenta de nuevo."). Investigación (systematic-debugging): log de Railway mostró `POST .../messages` → 200 OK (el streaming arranca bien, FastAPI ya respondió 200 antes de llamar a Gemini), descartando el path sin manejo de errores de `embed_text`/OpenAI — el fallo estaba dentro del `except gemini.GeminiError` de `chat/router.py`, que se traga el detalle real. Probado en vivo contra la API de Google con la key nueva: autentica correctamente (401 con la key vieja del `.env` local, luego confirmado que Railway y `.env` diferían), pero `gemini-2.5-flash` devuelve `404 "no longer available to new users"` con la key nueva — Google restringió ese modelo para proyectos nuevos, aunque siga apareciendo en `ListModels`. Probados en vivo los modelos disponibles con la key nueva: `gemini-2.0-flash-001` sin cuota (429), `gemini-flash-latest` y `gemini-3.5-flash` responden 200. Fix: `MODEL` en `app/integrations/gemini.py` cambia a `gemini-flash-latest` (alias que Google mantiene apuntando al Flash vigente, para no repetir este problema en la próxima rotación de key). De paso se confirmó que las tres keys nuevas (una vez sincronizadas entre Railway y `.env` local) autentican correctamente — el suite completo de `test_chat.py`/`test_metadata.py` (que llama a la API real de OpenAI para embeddings, sin mock) pasó 30/30 tras la sincronización. Tercera vez que un modelo hardcodeado de Google/Anthropic queda obsoleto sin aviso (Incrementos 7 y 9.1) |
| Incremento 23 | UX — spinner en respuesta pendiente del chat y al cambiar de conversación (F-02) | claude-sonnet-5 | 2026-08-06 | El desarrollador reportó dos síntomas por separado: (1) "cuando se carga un mensaje se ve abajo una parte sin nada"; (2) pidió un spinner mientras cargan los mensajes. Investigación: ambos reportes tenían la misma causa raíz. `ChatWindow.sendMessage` agrega la burbuja del asistente a `messages` con `content: ""` apenas se manda la consulta, y `ChatMessage` renderizaba `<p></p>` vacío para ese contenido — una burbuja en blanco visible hasta que llegara el primer chunk del streaming (la única señal de carga era un texto italic "Flippy está escribiendo…" *debajo* de esa burbuja vacía, fácil de pasar por alto). Fix: `ChatMessage` detecta `role === "assistant" && content === ""` y renderiza un spinner (`.spinner`, mismo patrón vino ya usado en `AdminDocumentTable`/`AdminFolderPanel`) en vez del párrafo vacío; se retiró el texto "Flippy está escribiendo…" de `ChatWindow` por quedar redundante. Además, `chat/page.tsx` no tenía ningún indicador mientras se pedía el historial de mensajes al cambiar de chat en el sidebar (solo existía el spinner de carga inicial de toda la página) — nuevo estado `isMessagesLoading`, pasado a `ChatWindow` como `isLoadingMessages`, que muestra `LoadingSpinner` centrado en el área de mensajes mientras se resuelve el fetch. 4 tests Jest nuevos (spinner en burbuja pendiente + reemplazo al llegar el primer chunk, spinner de `isLoadingMessages` — 78/78 total), `tsc --noEmit` limpio, build de producción limpio |
