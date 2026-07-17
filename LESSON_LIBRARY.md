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
