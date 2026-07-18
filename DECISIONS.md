# DECISIONS.md — Flippy

Registro de decisiones arquitecturales y de implementación.
Fuente de verdad junto con SPEC.md. No duplicar contenido del Spec aquí.

---

════════════════════════════════════════════════════════
📋 DECISIÓN — LLM split: Gemini 2.0 Flash (chat) + Claude 3.5 Sonnet (imágenes)
════════════════════════════════════════════════════════
Fecha: 2026-07-05
Decisión: Usar Google Gemini 2.0 Flash para respuestas RAG del chat y Anthropic Claude 3.5 Sonnet exclusivamente para análisis de imágenes adjuntas por el usuario.
Racional: Gemini 2.0 Flash ofrece menor costo por token para el volumen de consultas de chat RAG; Claude 3.5 Sonnet se mantiene para visión por su calidad en análisis multimodal combinado con corpus.
Alternativas consideradas: Claude 3.5 Sonnet para ambos casos (descartado por costo en chat de alto volumen); Gemini para ambos (descartado — análisis de imágenes con corpus requiere evaluación adicional).
Impacto: flippy-api requiere dos clientes LLM (langchain-google-genai + langchain-anthropic), dos variables de entorno (GOOGLE_API_KEY + ANTHROPIC_API_KEY), lógica de routing en el endpoint de chat según presencia de imagen adjunta.
════════════════════════════════════════════════════════

════════════════════════════════════════════════════════
📋 DECISIÓN — Estructura base como monorepo de trabajo (Incremento 1)
════════════════════════════════════════════════════════
Fecha: 2026-07-05
Decisión: Scaffoldear flippy-api (FastAPI) y flippy-web (Next.js 14 App Router + TS) como carpetas dentro del mismo repo de trabajo, aunque §7 del Spec declara 2 repos GitHub privados separados.
Racional: Permite iterar rápido en un solo repo durante desarrollo; la separación en repos independientes se hace al momento del primer deploy a Railway, sin bloquear el inicio de $build.
Alternativas consideradas: crear 2 repos Git desde el día 1 (descartado por ahora — agrega fricción sin beneficio inmediato en esta etapa).
Impacto: estructura `flippy-api/` (FastAPI, health check en `/api/v1/health`, pytest configurado) y `flippy-web/` (Next.js 14, PWA manifest + service worker básico, `services/api.ts` como único punto de llamadas al backend, Jest configurado). Ambas suites de tests verdes (1 passed cada una). .gitignore actualizado para ambos servicios.
════════════════════════════════════════════════════════

════════════════════════════════════════════════════════
📋 DECISIÓN — Migraciones SQL vía Session Pooler de Supabase (Incremento 2)
════════════════════════════════════════════════════════
Fecha: 2026-07-06
Decisión: Provisionar las 6 tablas de §4 (users, chats, messages, documents, document_chunks, subscriptions) e índices (IVFFlat + B-tree) contra el proyecto Supabase real del cliente, usando psycopg2 + connection string del Session Pooler, no la conexión directa.
Racional: la conexión directa de Supabase (`db.xxx.supabase.co`) requiere IPv6 — falla por DNS en redes IPv4-only (confirmado en este entorno). El Session Pooler (`aws-0-...pooler.supabase.com`) resuelve por IPv4 y soporta DDL sin restricciones en modo Session.
Alternativas consideradas: Transaction pooler (descartado — no siempre soporta DDL de forma confiable); Supabase CLI `db push` (descartado por ahora — agrega dependencia de instalación adicional sin beneficio claro en esta etapa).
Impacto: `SUPABASE_DB_URL` documentada en `.env.example` con la advertencia de usar el pooler; `scripts/apply_migrations.py` aplica migraciones en orden; `app/core/db.py` expone `get_db_connection()`; 3 tests pytest verdes (incluye conexión real y verificación de existencia de tablas) — primer test de integración real contra infraestructura del cliente.
════════════════════════════════════════════════════════

════════════════════════════════════════════════════════
📋 DECISIÓN — F-01 con Supabase Auth (GoTrue) + validación JWKS (Incremento 3)
════════════════════════════════════════════════════════
Fecha: 2026-07-09
Decisión: Implementar F-01 (registro/login) delegando la gestión de credenciales a Supabase Auth (GoTrue) en vez de un JWT propio con bcrypt. FastAPI actúa como proxy hacia `/auth/v1/*` de Supabase y valida los JWT resultantes contra el JWKS público del proyecto (ES256), no contra un secreto compartido. El rol administrador se resuelve por lista `ADMIN_EMAILS` en vez de una tabla de roles/permisos granular.
Racional: el cliente compartió una API existente (`examples/main-api`) como modelo estructural (separación router/services/model), pero esa API es multi-tenant con JWT propio (bcrypt + refresh tokens en tabla propia) y permisos granulares de un dominio distinto (clínicas estéticas) — incompatible con SPEC.md §2/§5/§11 (Flippy es single-tenant, roles simples). Entre JWT propio y Supabase Auth, se eligió Supabase Auth por ser más seguro: hashing de contraseñas, rotación de refresh tokens y (a futuro) verificación de email/reset de password quedan a cargo de Supabase en vez de código propio a mantener. Se descubrió en la práctica que el proyecto usa firma asimétrica ES256 (JWKS), no el secreto HS256 "legacy" — la validación se implementó contra JWKS, que además rota automáticamente sin gestionar un secreto.
Alternativas consideradas: JWT propio replicando el ejemplo del cliente (descartado — mayor superficie de seguridad, sin reset de password ni verificación de email); tabla de roles/permisos granular como el ejemplo (descartado — sobre-ingeniería para los 5 roles simples de §2).
Impacto: `app/integrations/supabase_auth.py` (wrapper httpx sobre GoTrue), `app/core/security.py` (validación JWKS + `require_admin`), `app/modules/auth/{model,services,router}.py`, migración 0004 (FK `users.id` → `auth.users.id`), `ADMIN_EMAILS` en `.env.example`. F-01 actualizado en SPEC.md para reflejar el flujo real. 6 tests pytest verdes contra Supabase real (registro, login, refresh, /me, password incorrecto, sin token), con limpieza automática de usuarios de prueba vía Admin API.
Hallazgos operativos resueltos en el camino: (1) SSL_CERTIFICATE_VERIFY_FAILED por interceptación TLS local — resuelto con `pip-system-certs` (usa el almacén de certificados de Windows); (2) rate limit de emails de confirmación de Supabase agotado en pruebas — resuelto desactivando "Confirm email" en Supabase Auth settings, consistente con el flujo F-01 de acceso inmediato tras registro.
════════════════════════════════════════════════════════

════════════════════════════════════════════════════════
🚨 DECISIÓN DE SEGURIDAD — Habilitar RLS en las 6 tablas públicas (Incremento 3.1)
════════════════════════════════════════════════════════
Fecha: 2026-07-09
Decisión: Habilitar Row-Level Security (RLS) en users, chats, messages, documents, document_chunks y subscriptions, sin policies (deny-all para anon/authenticated vía REST).
Racional: Supabase notificó por email una vulnerabilidad crítica (rls_disabled_in_public) — con RLS deshabilitado, cualquiera con la URL del proyecto y la anon key podía leer/editar/borrar todas las filas de las 6 tablas vía la API REST pública de PostgREST. flippy-api usa exclusivamente SUPABASE_SERVICE_ROLE_KEY, que bypassea RLS por diseño de Postgres/Supabase — habilitar RLS sin policies no afecta al backend y cierra el acceso público por completo.
Alternativas consideradas: escribir policies granulares por rol antes de habilitar RLS (descartado por ahora — innecesario mientras el único cliente de estas tablas sea flippy-api con service_role; se revisará si en el futuro el frontend necesita leer Supabase directamente, lo cual hoy no ocurre por regla de arquitectura de CLAUDE.md).
Impacto: migración 0005_enable_rls.sql aplicada contra Supabase real; verificado rowsecurity=true en pg_tables para las 6 tablas; suite de tests (service_role) sigue en verde tras el cambio — 0 regresiones.
════════════════════════════════════════════════════════

════════════════════════════════════════════════════════
📋 DECISIÓN — Reconstrucción de UI de chat fiel a brandbook + prototipo del cliente (Incremento 4)
════════════════════════════════════════════════════════
Fecha: 2026-07-12
Decisión: Reescribir por completo la UI de chat (construida inicialmente sin revisar docs/ a fondo) para ser fiel al brandbook formal (docs/Flipping Master - Manual de Marca.pdf) y al prototipo HTML del cliente (docs/flippy_prototipo_v4_claro (1).html), ambos presentes en el repo pero no revisados hasta este punto del desarrollo.
Racional: SPEC.md §C había sido aprobado con varios valores [proposed] por el desarrollador ante la ausencia percibida de brandbook formal. Al iniciar el incremento de UI se descubrió que sí existía un manual de marca completo y un prototipo aprobado por el cliente en docs/, con colores exactos, reglas de contraste, tipografía y estructura de pantallas (app móvil con navegación por pestañas, no el layout de escritorio con sidebar fijo construido inicialmente). Se optó por reconstruir en vez de parchear para no arrastrar una base visual incorrecta a incrementos futuros.
Alternativas consideradas: mantener el layout de escritorio ya construido y solo corregir colores (descartado por el desarrollador — se prefirió fidelidad completa al prototipo aprobado por el cliente).
Impacto: SPEC.md §C reescrito con Brand Token Sheet [explicit] (reemplaza la versión [proposed] anterior); logo real extraído del prototipo (public/icons/logo-shield.png); componentes reescritos: ChatMessage, ChatInput, ChatSidebar (+búsqueda, agrupación por fecha, footer de usuario), nuevos ChatHeader y ChatChips; layout responsive (mobile: pantallas separadas con toggle fiel al prototipo; desktop: sidebar persistente, cumple criterio §8 de testing en Chrome desktop). Verificación visual con Playwright (screenshots reales + estilos computados vía chromium headless, ya que no había chromium-cli disponible en este entorno) detectó y permitió corregir 2 bugs de CSS invisibles en los tests unitarios: (1) las custom properties --font-cormorant/--font-lato se declaraban en <body> pero --font-primary/--font-secondary las referenciaban desde :root (<html>), un nivel más arriba, causando fallback silencioso a fuentes del sistema — resuelto moviendo las clases de Next Font a <html>; (2) el <nav> del sidebar no tenía width:100%, causando que se encogiera a su contenido cuando el padre pasaba a display:flex en mobile, dejando una franja de fondo visible — resuelto agregando width:100% explícito.
════════════════════════════════════════════════════════

════════════════════════════════════════════════════════
📋 DECISIÓN — Deploy a Railway como 2 servicios desde monorepo
════════════════════════════════════════════════════════
Fecha: 2026-07-13
Decisión: Deployar flippy-api y flippy-web como 2 servicios Railway separados dentro del mismo proyecto, ambos apuntando al repo único flippy en GitHub, diferenciados por Root Directory (flippy-api / flippy-web respectivamente).
Racional: consistente con la decisión del Incremento 1 de mantener el monorepo de trabajo — Railway soporta múltiples servicios desde un mismo repo vía Root Directory, evitando la fricción de separar en 2 repos GitHub distintos (previsto en §7 pero pospuesto).
Alternativas consideradas: 2 repos GitHub separados como indica §7 originalmente (pospuesto — se revisará antes de la entrega final al cliente si corresponde separar).
Impacto: flippy-api con start command `uvicorn main:app --host 0.0.0.0 --port $PORT` y variables de entorno de producción cargadas manualmente en Railway; flippy-web con `NEXT_PUBLIC_API_BASE_URL` apuntando al dominio público de flippy-api. Ambos servicios verificados end-to-end: /api/v1/health → 200, /chat → renderiza correctamente.
════════════════════════════════════════════════════════

════════════════════════════════════════════════════════
📋 DECISIÓN — Pipeline de ingesta de documentos vía httpx directo (Incremento 5)
════════════════════════════════════════════════════════
Fecha: 2026-07-13
Decisión: Implementar la ingesta de documentos (F-05 backend) con wrappers httpx propios sobre Supabase Storage REST API y OpenAI embeddings REST API, en vez de instalar los SDKs oficiales (supabase-py, openai). Chunking con tiktoken (tokenización real de OpenAI) en vez de conteo aproximado por palabras/caracteres. Procesamiento en background task de FastAPI (no bloquea la respuesta al admin).
Racional: consistente con el patrón ya usado en supabase_auth.py (Incremento 3) — wrappers delgados evitan dependencias pesadas y mantienen el control total sobre errores/timeouts. tiktoken asegura que el chunking de 500 tokens (SPEC.md §5) sea exacto y no una aproximación, evitando chunks que excedan el límite real de contexto.
Alternativas consideradas: SDK oficial de OpenAI (descartado — dependencia más pesada para un solo endpoint usado); conteo de tokens por palabras (descartado — impreciso, podría generar chunks fuera de rango).
Impacto: `app/integrations/supabase_storage.py`, `app/integrations/openai_embeddings.py`, `app/modules/documents/{chunking,parsers,model,services,router}.py`. Nuevas dependencias: pdfplumber, python-docx, tiktoken, python-multipart. Límite de 20MB por archivo agregado (hallazgo propio de seguridad — no había límite antes, riesgo de DoS por upload). 11 tests pytest verdes contra Storage/OpenAI/pgvector reales.
════════════════════════════════════════════════════════

════════════════════════════════════════════════════════
📋 DECISIÓN — Panel de admin sin prototipo de referencia (Incremento 6)
════════════════════════════════════════════════════════
Fecha: 2026-07-13
Decisión: Maquetar /login y /admin con los tokens de marca ya aprobados (§C) pero sin un layout de referencia del cliente, ya que el prototipo HTML solo cubre las pantallas de usuario final (inicio/chat/historial/acceso socios) y no el panel de administración.
Racional: a diferencia del Incremento 4 (donde se descartó una UI ya construida por no seguir el prototipo), acá no existe prototipo que contradecir — es una superficie interna (solo la usa el admin) sin peso de marca cliente-facing. Se prioriza funcionalidad clara sobre fidelidad visual estricta.
Alternativas consideradas: esperar a que el cliente provea un mockup del panel de admin antes de construir (descartado — bloquearía innecesariamente el avance de Hito 2; el panel de admin no es una superficie que el cliente final (socios) vea).
Impacto: app/login/page.tsx (primera pieza real de F-01 frontend — hasta ahora solo existía el backend), app/admin/page.tsx, components/AdminUploadForm.tsx, components/AdminDocumentTable.tsx, services/api.ts extendido con apiUpload/apiDelete/ApiError. Polling cada 4s mientras haya documentos en processing, sin WebSocket/SSE para esto (no lo justifica la frecuencia de uso — solo el admin sube documentos ocasionalmente). 28 tests Jest verdes (10 nuevos), build de producción limpio.
════════════════════════════════════════════════════════

════════════════════════════════════════════════════════
🚨 DECISIÓN — Fix crítico: CORS faltante bloqueaba todo el frontend (Incremento 6.1)
════════════════════════════════════════════════════════
Fecha: 2026-07-13
Decisión: Agregar CORSMiddleware a flippy-api, con origins permitidos configurables via WEB_ORIGIN (mas localhost:3000 fijo para desarrollo).
Racional: el usuario reportó error al hacer login en producción. Diagnóstico: flippy-api nunca tuvo CORSMiddleware configurado desde su creación (Incremento 1) — cualquier pedido del navegador desde flippy-web hacia flippy-api en un dominio distinto era bloqueado silenciosamente por la política de mismo origen, sin llegar siquiera a validar credenciales. Esto afectaba TODOS los endpoints, no solo login — bloqueaba también el panel de admin recién construido.
Alternativas consideradas: allow_origins=["*"] (descartado — con allow_credentials=True el spec de CORS prohíbe wildcard, y de todos modos es mas laxo de lo necesario para un solo frontend conocido).
Impacto: main.py agrega CORSMiddleware; config.py expone cors_origins (localhost:3000 + WEB_ORIGIN); WEB_ORIGIN documentado en .env.example, debe cargarse en Railway (flippy-api) con el dominio de flippy-web. 2 tests pytest nuevos (origin permitido / origin no permitido).
════════════════════════════════════════════════════════

════════════════════════════════════════════════════════
📋 DECISIÓN — Chat RAG real reemplaza el mock; gemini-2.0-flash descontinuado (Incremento 7)
════════════════════════════════════════════════════════
Fecha: 2026-07-14
Decisión: Implementar F-02 (consulta de chat RAG) de punta a punta — módulo app/modules/chat (chats/mensajes con ownership, título autogenerado), embedding de consulta + búsqueda coseno en document_chunks (top 5), prompt con historial (últimos 10 mensajes) enviado a Gemini con streaming SSE real, y wiring del frontend (ChatWindow + chat/page.tsx) contra los endpoints reales en vez de mockChatData. Usar gemini-2.5-flash en vez de gemini-2.0-flash (SPEC.md §5/§7).
Racional: al probar la integración contra la API real de Google (no solo mocks), gemini-2.0-flash devolvió 404 "no longer available" — Google lo descontinuó. Se listaron los modelos disponibles vía la API con la key real y se confirmó gemini-2.5-flash como el Flash estable vigente (GA, no preview). Se prioriza un modelo estable por sobre seguir al pie de la letra un nombre de modelo ya no soportado por el proveedor.
Alternativas consideradas: gemini-flash-latest (alias, descartado por preferir fijar una versión concreta para reproducibilidad); modelos preview (3.x) descartados por no ser aptos para producción todavía.
Hallazgo operativo: la cuenta de Google AI Studio requirió habilitar billing (free tier tenía límite 0 para este modelo) — resuelto por el desarrollador antes de poder probar en vivo.
Impacto: app/integrations/gemini.py (nuevo, streaming SSE con decodificación UTF-8 explícita a nivel de bytes — iter_lines() de httpx puede adivinar mal el encoding en fragmentos SSE pequeños), app/modules/chat/{model,services,router}.py (nuevo), api/v1/router.py registra el router. Frontend: ChatWindow.tsx consume el SSE vía apiStream y renderiza incrementalmente; chat/page.tsx reemplaza mocks por /api/v1/chats real; lib/mockChatData.ts eliminado (sin usos). F-04 (imagen) fuera de alcance — aviso explícito si se adjunta imagen. jest.setup.ts agrega polyfills de TextEncoder/TextDecoder/ReadableStream (faltantes en jsdom, necesarios para testear el parseo del stream SSE). Verificado end-to-end contra infraestructura real (login, chat, streaming, persistencia) fuera de los tests automatizados. 17 tests pytest (4 nuevos) y 34 tests Jest (7 nuevos) verdes, build de producción limpio.
════════════════════════════════════════════════════════

════════════════════════════════════════════════════════
📋 DECISIÓN — Eliminar y renombrar chat vía menú kebab (Incremento 8)
════════════════════════════════════════════════════════
Fecha: 2026-07-16
Decisión: Implementar F-03 completo (renombrar + eliminar chat), reportado por el usuario como "no puedo eliminar el chat". Backend: PATCH /api/v1/chats/{id} y DELETE /api/v1/chats/{id} en app/modules/chat, ambos validan ownership (user_id) devolviendo 404 si el chat es de otro usuario o no existe. El borrado de mensajes es cascada automática vía la FK ya existente (messages.chat_id → chats.id on delete cascade en 0002_tables.sql) — no se necesitó lógica adicional de limpieza. Frontend: ChatSidebar gana menú contextual (kebab), input de renombrado inline y modal de confirmación propio (sin librería) antes de eliminar.
Racional: investigación (systematic-debugging) confirmó que el ícono kebab del sidebar era puramente decorativo desde su introducción en el Incremento 4 — ninguna de las dos acciones tenía endpoint de backend ni handler de frontend. No era una regresión sino una funcionalidad nunca construida.
Alternativas consideradas: soft-delete (columna deleted_at) — descartado, no hay requerimiento de recuperar chats eliminados ni de retención específica para esta entidad; usar window.confirm() nativo del navegador — descartado a favor de un modal propio consistente con la identidad visual de la app.
Comportamiento del chat activo al eliminarlo (definido con el usuario): si la vista actual corresponde al chat eliminado, la pantalla queda en blanco (sin auto-seleccionar otro chat); si el usuario está viendo otro chat, no cambia nada.
Impacto: flippy-api: model.py (ChatRename), services.py (rename_chat, delete_chat), router.py (rutas PATCH/DELETE), 5 tests pytest nuevos contra Supabase real (rename propio/ajeno, delete propio/ajeno + cascada de mensajes, requiere auth). flippy-web: services/api.ts (apiPatch nuevo), ChatSidebar.tsx + .module.css (menú, input de rename, modal de confirmación), chat/page.tsx (handleRenameChat/handleDeleteChat), 3 tests Jest nuevos. SPEC.md §3 F-03 ampliado con los pasos 3-6 (antes solo mencionaba renombrar sin que existiera). 22/22 tests pytest y 37/37 tests Jest verdes, tsc sin errores.
════════════════════════════════════════════════════════

════════════════════════════════════════════════════════
📋 DECISIÓN — Fix: menú kebab sin listener de clic externo (Incremento 8.1)
════════════════════════════════════════════════════════
Fecha: 2026-07-16
Decisión: Agregar un `useEffect` en ChatSidebar que registra un listener `mousedown` en `document` mientras haya un menú kebab abierto (`openMenuId`), y lo cierra si el clic ocurre fuera del `<li data-menu-id={chat.id}>` correspondiente (`Element.closest`).
Racional: el usuario reportó que el popup de opciones quedaba abierto al hacer clic en otro lugar. El menú (Incremento 8) solo tenía lógica de cierre al re-tocar el mismo kebab o al elegir Renombrar/Eliminar — nunca se contempló el clic fuera. Se usa `mousedown` (no `click`) para que el cierre ocurra antes de que la acción del elemento clickeado se dispare, evitando estados intermedios inconsistentes.
Alternativas consideradas: un ref por ítem con `useRef` — descartado por requerir un array/mapa de refs dinámico para una lista variable de chats; el atributo `data-menu-id` + `closest()` logra lo mismo sin esa complejidad.
Impacto: flippy-web/components/ChatSidebar.tsx (useEffect + atributo data-menu-id en el `<li>`), 1 test Jest nuevo (clic en document.body cierra el menú). 38/38 tests Jest verdes.
════════════════════════════════════════════════════════

════════════════════════════════════════════════════════
📋 DECISIÓN — F-04 análisis de imagen: Claude en streaming (no "llamada estándar"), bucket privado con URLs firmadas (Incremento 9)
════════════════════════════════════════════════════════
Fecha: 2026-07-17
Decisión: Implementar F-04 completo. Backend nuevo: app/integrations/anthropic_vision.py (wrapper httpx sobre la Messages API de Claude 3.5 Sonnet con streaming SSE, mismo patrón que gemini.py — sin LangChain, consistente con el precedente del Incremento 7); supabase_storage.py generalizado para aceptar un parámetro `bucket` en vez de la constante fija `documents`, más create_signed_url() nuevo; bucket privado nuevo `chat-attachments` para las imágenes que suben los usuarios en el chat; endpoint POST /{chat_id}/messages/image (multipart: file + content opcional) que sube la imagen, arma el prompt multimodal con los chunks RAG del texto adjunto (si lo hay) y transmite la respuesta de Claude en streaming, mismo formato de evento SSE que el chat de texto.
Racional (streaming): SPEC.md §7 documentaba "llamada estándar vía Anthropic SDK" para este caso (no streaming), pero CLAUDE.md establece como regla de producto "Streaming en todas las respuestas del chat (SSE)" sin excepción para imágenes. Se prioriza la regla de producto (más específica al comportamiento visible del chat) por sobre el detalle técnico de integración del documento original, y se gana consistencia: el frontend reutiliza el mismo parser de SSE para ambos casos (extraído a consumeStream en ChatWindow.tsx) en vez de tener dos rutas de UI distintas.
Racional (bucket privado + URL firmada en cada lectura, no en el upload): el bucket `documents` ya es privado por precedente (Incremento 1/5); replicar esa política para imágenes de chat evita exponer fotos de usuarios via URL pública adivinable. Guardar el path (no una URL firmada) en `messages.image_url` y resolverlo a una URL firmada de corta duración en cada `list_messages` evita que el historial se rompa cuando la firma expira — el requisito F-01 es "historial persistente... desde cualquier dispositivo" indefinidamente, una URL firmada guardada una sola vez no lo cumpliría.
Alternativas consideradas: bucket público con paths UUID no listables (descartado — mismo nivel de "seguridad por oscuridad" que ya se evitó para documentos, sin necesidad real de que sea público); firmar la URL una sola vez al subir la imagen y guardarla tal cual (descartado por la razón de expiración de arriba); usar langchain-anthropic (descartado, mismo argumento que gemini.py: un wrapper httpx delgado es más simple y ya es el patrón establecido en el proyecto).
Bloqueo de verificación: ANTHROPIC_API_KEY está vacía en el entorno — es un requisito del cliente pendiente (cuenta Anthropic con billing activo, ver documento de proyecto §9). Los tests nuevos mockean anthropic_vision.stream_vision (mismo patrón que test_send_message_streams_and_persists ya usa para Gemini); la subida a Storage y la firma de URL sí se ejecutan contra Supabase real. No hay verificación E2E contra la API real de Claude todavía — pendiente hasta que el cliente complete el requisito.
Impacto: flippy-api: anthropic_vision.py (nuevo), supabase_storage.py (bucket parametrizado + create_signed_url), chat/services.py (upload_chat_image, _resolve_image_url, build_vision_messages, constantes CHAT_IMAGES_BUCKET/SIGNED_URL_EXPIRES_IN/DEFAULT_IMAGE_CAPTION), chat/router.py (POST /{chat_id}/messages/image, límite 5 MB). flippy-web: services/api.ts (apiStreamUpload), ChatWindow.tsx (consumeStream extraído, placeholder de F-04 reemplazado). SPEC.md §3 F-04 actualizado con el detalle de bucket/streaming. 5 tests pytest nuevos (27/27 total) y 2 tests Jest nuevos (39/39 total) verdes, build de producción limpio.
════════════════════════════════════════════════════════

════════════════════════════════════════════════════════
📋 DECISIÓN — Fix proactivo: modelo Claude desactualizado (Incremento 9.1)
════════════════════════════════════════════════════════
Fecha: 2026-07-17
Decisión: Cambiar MODEL en anthropic_vision.py de claude-3-5-sonnet-20241022 (el id que especifica SPEC.md §7, sin fecha de revisión) a claude-sonnet-5.
Racional: al correr $verify tras cerrar el Incremento 9, una búsqueda del lineup vigente de Anthropic (julio 2026) confirmó que el roster actual es Fable 5 / Opus 4.8 / Sonnet 5 / Haiku 4.5 — ningún resultado listó claude-3-5-sonnet-20241022 como modelo activo. Un id de octubre 2024 sin verificar contra una API que ya retiró gemini-2.0-flash en circunstancias casi idénticas (Incremento 7) es un riesgo conocido, no hipotético: sin este fix, F-04 fallaría con 404 en el primer uso real, exactamente como pasó con Gemini.
Diferencia importante con el fix de Gemini: aquella corrección se hizo después de un 404 real contra la API en vivo. Esta se hace sin key configurada — es una corrección preventiva basada en evidencia externa (WebSearch) y en el roster de modelos del propio contexto de sesión, no una confirmación directa. Se documenta explícitamente como pendiente de reconfirmación una vez el cliente complete el requisito de cuenta Anthropic con billing (ver §9 del documento de proyecto).
Alternativas consideradas: dejar claude-3-5-sonnet-20241022 y esperar a que falle en vivo para corregir (descartado — ya se conoce el patrón de falla exacto por el caso Gemini, no tiene sentido repetir el mismo error evitable); usar un alias tipo "claude-latest" si existiera (no se encontró evidencia de que la API de Anthropic ofrezca ese alias, a diferencia de Gemini con gemini-flash-latest).
Impacto: flippy-api/app/integrations/anthropic_vision.py (constante MODEL + comentario explicando la desviación). SPEC.md §7 (sección Anthropic reescrita con la desviación documentada) y §A Delta Log (entrada 5). Sin cambios de tests (el modelo no se ejercita en los tests mockeados).
════════════════════════════════════════════════════════
