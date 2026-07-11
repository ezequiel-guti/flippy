-- Tablas principales (SPEC.md §4)

create table if not exists users (
    id uuid primary key default uuid_generate_v4(),
    email text unique not null,
    plan text not null default 'gratuito' check (plan in ('gratuito', 'pago')),
    status text not null default 'gratuito' check (status in ('activo', 'en_mora', 'gratuito', 'cancelado')),
    mp_subscription_id text,
    mp_customer_id text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists chats (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null references users(id) on delete cascade,
    title text not null default 'Nuevo chat',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists messages (
    id uuid primary key default uuid_generate_v4(),
    chat_id uuid not null references chats(id) on delete cascade,
    role text not null check (role in ('user', 'assistant')),
    content text not null,
    image_url text,
    created_at timestamptz not null default now()
);

create table if not exists documents (
    id uuid primary key default uuid_generate_v4(),
    name text not null,
    type text not null check (type in ('pdf', 'docx', 'txt', 'image')),
    storage_path text not null,
    status text not null default 'processing' check (status in ('processing', 'ready', 'error')),
    chunk_count integer not null default 0,
    created_at timestamptz not null default now()
);

create table if not exists document_chunks (
    id uuid primary key default uuid_generate_v4(),
    document_id uuid not null references documents(id) on delete cascade,
    content text not null,
    embedding vector(1536),
    chunk_index integer not null,
    metadata jsonb not null default '{}'::jsonb
);

create table if not exists subscriptions (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null references users(id) on delete cascade,
    mp_subscription_id text not null,
    status text not null check (status in ('authorized', 'paused', 'cancelled')),
    next_payment_date date,
    last_event text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
