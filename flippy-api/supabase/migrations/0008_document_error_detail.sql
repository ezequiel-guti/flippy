-- Detalle del error de ingesta cuando documents.status = 'error' (SPEC.md §4, RN-06)

alter table documents add column if not exists error_detail text;
