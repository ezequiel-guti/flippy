-- Marca de inicio del intento de procesamiento actual (SPEC.md §4, RN-06) —
-- permite distinguir un documento realmente colgado en 'processing' de uno
-- que arrancó hace instantes.

alter table documents add column if not exists processing_started_at timestamptz;

update documents set processing_started_at = created_at where processing_started_at is null;
