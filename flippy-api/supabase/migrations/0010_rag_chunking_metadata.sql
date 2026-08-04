-- Chunking por estrategia + metadatos tipados para filtrado por intención,
-- y swap de índice vectorial IVFFlat -> HNSW (SPEC_RAG.md §1, §2, §9 delta #3).
-- apply_migrations.py reaplica todos los archivos en cada corrida: todo acá
-- debe ser idempotente, incluido el swap de índice (solo debe reconstruirse
-- una vez, no en cada deploy).

-- 1. Enum de estrategia
do $$
begin
    create type chunking_strategy as enum ('atomic', 'by_section', 'by_topic', 'by_qa_pair', 'fixed_500');
exception when duplicate_object then null;
end $$;

-- 2. Columnas nuevas en documents
alter table documents
    add column if not exists strategy chunking_strategy not null default 'fixed_500',
    add column if not exists strategy_source text not null default 'inferred'
        check (strategy_source in ('explicit', 'inferred')),
    add column if not exists strategy_reason text,
    add column if not exists token_count integer,
    add column if not exists indexed_at timestamptz;

-- 3. Metadatos tipados en document_chunks (metadata jsonb se mantiene para
-- datos no consultables; los campos usados en filtrado pasan a columnas nativas)
alter table document_chunks
    add column if not exists fecha_vigencia date,
    add column if not exists tipo text,
    add column if not exists moneda text check (moneda in ('ARS', 'USD') or moneda is null),
    add column if not exists region text,
    add column if not exists es_primaria boolean default false,
    add column if not exists header_text text,
    add column if not exists token_count integer;

-- 4. Índices de pre-filtrado
create index if not exists idx_chunks_fecha on document_chunks (fecha_vigencia desc nulls last);
create index if not exists idx_chunks_tipo on document_chunks (tipo);
create index if not exists idx_chunks_region on document_chunks (region);
create index if not exists idx_chunks_primaria on document_chunks (es_primaria) where es_primaria = true;

create index if not exists idx_chunks_mercado
    on document_chunks (tipo, region, fecha_vigencia desc)
    where tipo in ('dato_mercado', 'costo');

-- 5. Índice vectorial: IVFFlat -> HNSW (SPEC_RAG.md §2.6 — degrada con
-- pre-filtrado y requiere reentrenamiento con corpus creciente)
do $$
begin
    if not exists (
        select 1
        from pg_class ic
        join pg_am am on am.oid = ic.relam
        where ic.relname = 'document_chunks_embedding_idx' and am.amname = 'hnsw'
    ) then
        execute 'drop index if exists document_chunks_embedding_idx';
        execute 'create index document_chunks_embedding_idx
                    on document_chunks
                    using hnsw (embedding vector_cosine_ops)
                    with (m = 16, ef_construction = 64)';
    end if;
end $$;
