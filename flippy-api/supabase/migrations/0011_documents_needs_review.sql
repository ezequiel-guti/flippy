-- Flag de revisión manual para metadatos de baja confianza (SPEC_RAG.md §6.5).
-- No estaba en la migración 002 original (0010) — ese bloque de SQL solo cubría
-- estrategia de chunking y columnas de document_chunks, no este flag a nivel documento.

alter table documents
    add column if not exists needs_review boolean not null default false;

create index if not exists idx_documents_needs_review on documents (needs_review) where needs_review = true;
