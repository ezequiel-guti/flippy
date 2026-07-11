# Lesson Library

## Entries

### L-01 — Supabase direct connection falla por DNS en redes IPv4-only
**Category:** Data & Debugging
**Signal:** Al conectar a Supabase Postgres (psycopg2 o cualquier cliente) y ver el error `could not translate host name "db.xxx.supabase.co" to address` — no es un typo ni una credencial incorrecta: la conexión directa de Supabase exige IPv6, y muchas redes/entornos son IPv4-only.
**Principle:** Para conexiones directas a Postgres desde entornos sin soporte IPv6, usar el Session Pooler de Supabase (`aws-0-...pooler.supabase.com`, usuario `postgres.<project-ref>`) en vez del host directo (`db.xxx.supabase.co`). El modo Session del pooler soporta DDL sin restricciones; el modo Transaction no siempre.
**Tags:** #stack/supabase #stack/postgres #phase/build #flippy

---
