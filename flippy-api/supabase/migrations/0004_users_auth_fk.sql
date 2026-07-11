-- Enlaza public.users.id con auth.users.id (Supabase Auth es la fuente de verdad de la identidad)
alter table users
    drop constraint if exists users_id_fkey;

alter table users
    add constraint users_id_fkey foreign key (id) references auth.users (id) on delete cascade;

alter table users
    alter column id drop default;
