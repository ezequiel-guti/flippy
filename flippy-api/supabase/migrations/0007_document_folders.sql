-- Carpetas y subcarpetas para organizar documentos del corpus (SPEC.md §4, RN-08)

create table if not exists document_folders (
    id uuid primary key default uuid_generate_v4(),
    name text not null,
    parent_id uuid references document_folders(id) on delete restrict,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table documents add column if not exists folder_id uuid references document_folders(id) on delete restrict;

alter table document_folders enable row level security;
