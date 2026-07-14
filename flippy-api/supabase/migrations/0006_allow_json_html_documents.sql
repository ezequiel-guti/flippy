-- Permite subir documentos .json y .html al corpus (SPEC.md §4 documents.type)

alter table documents drop constraint if exists documents_type_check;
alter table documents add constraint documents_type_check
    check (type in ('pdf', 'docx', 'txt', 'json', 'html', 'image'));
