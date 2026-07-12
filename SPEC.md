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

---

## §2 — Usuarios y Roles

| Rol | Descripción | Acceso |
|-----|-------------|--------|
| **Usuario gratuito** | Miembro registrado sin suscripción activa | Chat limitado (definición pendiente — ver §12) |
| **Usuario pago** | Miembro con suscripción mensual activa | Chat completo + análisis de imágenes |
| **Usuario en mora** | Suscripción con pago rechazado, reintentos en curso | Acceso degradado al límite del plan gratuito |
| **Usuario cancelado** | Suscripción cancelada definitivamente | Solo plan gratuito |
| **Administrador** | Ezequiel / operador de la comunidad | Panel de gestión de documentos del corpus |

**Nota:** No hay rol "superadmin" ni multi-tenancy. Un solo cliente, un solo corpus, una sola comunidad.

---

## §3 — Flujos Funcionales

### F-01: Registro e inicio de sesión
1. El usuario accede a la PWA e ingresa email + contraseña
2. El frontend envía las credenciales a FastAPI (`/api/v1/auth/register` o `/login`), que las reenvía a Supabase Auth; Supabase Auth valida/crea el usuario y emite el JWT (access + refresh token) — FastAPI solo retransmite la respuesta, no maneja contraseñas
3. FastAPI crea/asegura la fila correspondiente en `public.users` (email, plan, status) enlazada por `id` a `auth.users`
4. El frontend guarda los tokens en localStorage
5. El usuario es redirigido al chat principal

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
3. El usuario puede renombrar un chat existente
4. El historial persiste por usuario y es accesible desde cualquier dispositivo

### F-04: Análisis de imagen (multimodal)
1. El usuario adjunta una imagen desde cámara o galería en la interfaz de chat
2. La imagen se sube a Supabase Storage y se referencia en el mensaje
3. FastAPI incluye la imagen en el prompt enviado a Claude 3.5 Sonnet (visión)
4. Claude analiza la imagen combinándola con los chunks RAG recuperados
5. La respuesta integra el análisis visual con el conocimiento del corpus

### F-05: Panel de administración de documentos
1. El administrador accede a la ruta protegida `/admin`
2. Puede subir archivos: PDF, Word (.docx), texto plano (.txt), imágenes (.jpg, .png)
3. FastAPI guarda el archivo en Supabase Storage y responde inmediatamente al cliente
4. Un background task procesa el archivo: extracción de texto → chunking → embeddings → pgvector
5. El administrador puede listar documentos (nombre, tipo, estado, cantidad de chunks)
6. El administrador puede eliminar un documento (elimina archivo, chunks y embeddings)

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

**documents**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | uuid PK | Identificador único del documento |
| name | text | Nombre del archivo |
| type | enum | `pdf` \| `docx` \| `txt` \| `image` |
| storage_path | text | Ruta en Supabase Storage |
| status | enum | `processing` \| `ready` \| `error` |
| chunk_count | integer | Cantidad de chunks generados |
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
| `gratuito` | Plan gratuito o sin suscripción | Limitado (ver §12 OD-01) |
| `cancelado` | Suscripción cancelada definitivamente | Solo plan gratuito |

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
- Solo el administrador puede subir, listar o eliminar documentos del corpus
- Al eliminar un documento se eliminan también sus chunks y embeddings
- El procesamiento es asincrónico — el admin recibe confirmación inmediata y el documento queda en estado `processing` hasta completar la ingesta

---

## §7 — Integraciones y APIs

### Google Gemini 2.0 Flash
- **Uso:** Generación de respuestas RAG (chat conversacional)
- **Modo:** Streaming vía Google Generative AI SDK (Python), retransmitido por FastAPI como SSE
- **Credencial:** `GOOGLE_API_KEY` solo en `flippy-api`, nunca expuesta al cliente
- **Integración LangChain:** `langchain-google-genai`

### Anthropic Claude 3.5 Sonnet
- **Uso:** Análisis de imágenes adjuntas por el usuario (multimodal / visión)
- **Modo:** Llamada estándar vía Anthropic SDK (Python) — solo cuando el mensaje incluye imagen
- **Credencial:** `ANTHROPIC_API_KEY` solo en `flippy-api`, nunca expuesta al cliente
- **Integración LangChain:** `langchain-anthropic`

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
| OD-01 | **Límite del plan gratuito:** ¿mensajes/día, mensajes/mes, o acceso a corpus reducido? | Virgilio (cliente) | Pendiente de confirmación |
| OD-02 | **Política de retención de PII:** ¿cuánto tiempo se conservan los datos de usuarios cancelados? | Virgilio + desarrollador | Pendiente para producción |

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
