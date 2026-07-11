# flippy-api

Backend FastAPI de Flippy: auth, chat RAG, ingesta de documentos, webhooks de Mercado Pago, streaming SSE.

## Desarrollo local

```bash
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements-dev.txt
cp .env.example .env       # completar valores
uvicorn main:app --reload
```

API disponible en `http://localhost:8000/api/v1/health`.

## Tests

```bash
pytest
```

## Variables de entorno

Ver `.env.example`. Ninguna credencial se commitea al repositorio.

`SUPABASE_DB_URL` debe usar el **Session Pooler** de Supabase (Project Settings -> Database ->
Connection string -> Session pooler), no la conexion directa: la conexion directa (`db.xxx.supabase.co`)
requiere IPv6 y falla por DNS en redes IPv4-only. El pooler usa `aws-0-...pooler.supabase.com` y
soporta DDL sin problemas en modo Session.

## Migraciones de base de datos

SQL en `supabase/migrations/`, aplicado en orden por nombre de archivo.

```bash
python scripts/apply_migrations.py
```

Requiere `SUPABASE_DB_URL` configurada en `.env` (ver nota arriba).

## Deploy

Railway, deploy continuo desde `main`. Ver SPEC.md §5 y §7.
