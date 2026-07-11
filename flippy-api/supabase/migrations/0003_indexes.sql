-- Indices (SPEC.md §4)

create index if not exists document_chunks_embedding_idx
    on document_chunks using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

create index if not exists messages_chat_id_idx on messages (chat_id);
create index if not exists chats_user_id_idx on chats (user_id);
