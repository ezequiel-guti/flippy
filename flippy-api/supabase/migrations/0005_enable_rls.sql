-- Cierra el hallazgo critico de Supabase "rls_disabled_in_public": sin RLS, cualquiera
-- con la URL del proyecto y la anon key puede leer/editar/borrar estas tablas via la API REST.
-- flippy-api usa SUPABASE_SERVICE_ROLE_KEY, que bypassea RLS por diseno, asi que habilitar RLS
-- sin policies no rompe nada del backend y bloquea el acceso publico (anon/authenticated) via REST.

alter table users enable row level security;
alter table chats enable row level security;
alter table messages enable row level security;
alter table documents enable row level security;
alter table document_chunks enable row level security;
alter table subscriptions enable row level security;
