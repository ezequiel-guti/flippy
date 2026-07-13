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
