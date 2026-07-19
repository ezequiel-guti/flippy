# Lesson Library

## Entries

### L-01 — Supabase direct connection falla por DNS en redes IPv4-only
**Category:** Data & Debugging
**Signal:** Al conectar a Supabase Postgres (psycopg2 o cualquier cliente) y ver el error `could not translate host name "db.xxx.supabase.co" to address` — no es un typo ni una credencial incorrecta: la conexión directa de Supabase exige IPv6, y muchas redes/entornos son IPv4-only.
**Principle:** Para conexiones directas a Postgres desde entornos sin soporte IPv6, usar el Session Pooler de Supabase (`aws-0-...pooler.supabase.com`, usuario `postgres.<project-ref>`) en vez del host directo (`db.xxx.supabase.co`). El modo Session del pooler soporta DDL sin restricciones; el modo Transaction no siempre.
**Tags:** #stack/supabase #stack/postgres #phase/build #flippy

---

### L-02 — Elementos de UI "fantasma": estilo interactivo sin handler conectado
**Category:** Best Practices / Workflow
**Signal:** Un ícono o botón en la UI tiene estilos hover/active y parece interactivo, pero carga `aria-hidden="true"` o no tiene ningún `onClick` — visualmente indistinguible de un elemento funcional, pero no dispara ninguna acción. Descubierto cuando el usuario reportó "no puedo eliminar el chat": el ícono kebab (⋮) del sidebar existía desde su creación (Incremento 4) con estilos completos, pero nunca tuvo handler ni endpoint de backend — no era una regresión, era una funcionalidad que nunca se construyó.
**Principle:** Al cerrar cualquier incremento de UI, verificar explícitamente que todo elemento con apariencia interactiva (cursor pointer, hover state, ícono de acción) tenga un handler conectado a un caso de uso real, o eliminarlo del markup. La revisión visual del componente terminado no detecta esto — hay que revisar el JSX/handlers, no solo el resultado renderizado.
**Tags:** #stack/react #stack/nextjs #phase/qa #phase/build #flippy

---

### L-03 — Mocks de LLM esconden bugs de contenido de prompt
**Category:** LLM Design / Data & Debugging
**Signal:** Una feature de LLM pasa toda la suite de tests (con la llamada al modelo mockeada vía `monkeypatch`) pero nunca se ejercitó con una llamada real end-to-end antes de darla por cerrada — especialmente cuando reutiliza infraestructura de otra feature (mismo `SYSTEM_PROMPT`, mismo cliente HTTP). Descubierto en F-04 (análisis de imagen): el endpoint reutilizaba el `SYSTEM_PROMPT` del chat de texto RAG ("respondé ÚNICAMENTE basándote en el contexto provisto"), y Claude se negaba a describir imágenes sin contexto de corpus relacionado — comportamiento opuesto al requerido. Los tests mockeados nunca lo detectaron porque no ejercitan el contenido real del prompt contra el modelo.
**Principle:** Cuando una feature de LLM reutiliza infraestructura (prompt, cliente, wrapper) de otra ya existente, correr al menos una llamada real end-to-end contra el modelo antes de cerrar el incremento — los mocks validan el flujo de código (requests, parsing, persistencia) pero no pueden detectar que el contenido de un prompt es incompatible con el nuevo caso de uso. Si no hay credenciales disponibles todavía, dejarlo marcado explícitamente como "pendiente de verificación E2E" en vez de darlo por cerrado.
**Tags:** #stack/anthropic #stack/llm #phase/qa #phase/build #flippy

---
