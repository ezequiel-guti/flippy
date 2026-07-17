import json
import uuid

from app.core.db import get_db_connection
from app.integrations import supabase_storage

TOP_K_CHUNKS = 5
HISTORY_LIMIT = 10
TITLE_MAX_LENGTH = 60
DEFAULT_TITLE = "Nuevo chat"
DEFAULT_IMAGE_CAPTION = "Imagen adjunta"

CHAT_IMAGES_BUCKET = "chat-attachments"
SIGNED_URL_EXPIRES_IN = 3600

SYSTEM_PROMPT = (
    "Sos Flippy, el asistente de la comunidad educativa inmobiliaria. "
    "Respondé UNICAMENTE basandote en el contexto provisto a continuacion. "
    "No menciones de donde proviene la informacion ni cites documentos o fuentes. "
    "Si no encontras la respuesta en el contexto, decilo claramente y no inventes informacion."
)


class ChatService:
    @staticmethod
    def list_chats(user_id: str) -> list[dict]:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "select id, title, updated_at from chats where user_id = %s order by updated_at desc",
                    (user_id,),
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        return [{"id": str(r[0]), "title": r[1], "updated_at": r[2].isoformat()} for r in rows]

    @staticmethod
    def create_chat(user_id: str, title: str = DEFAULT_TITLE) -> dict:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into chats (user_id, title)
                    values (%s, %s)
                    returning id, title, updated_at
                    """,
                    (user_id, title),
                )
                row = cur.fetchone()
            conn.commit()
        finally:
            conn.close()

        return {"id": str(row[0]), "title": row[1], "updated_at": row[2].isoformat()}

    @staticmethod
    def get_chat(chat_id: str, user_id: str) -> dict | None:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "select id, title, updated_at from chats where id = %s and user_id = %s",
                    (chat_id, user_id),
                )
                row = cur.fetchone()
        finally:
            conn.close()

        if not row:
            return None
        return {"id": str(row[0]), "title": row[1], "updated_at": row[2].isoformat()}

    @staticmethod
    def rename_chat(chat_id: str, user_id: str, title: str) -> dict | None:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    update chats set title = %s
                    where id = %s and user_id = %s
                    returning id, title, updated_at
                    """,
                    (title, chat_id, user_id),
                )
                row = cur.fetchone()
            conn.commit()
        finally:
            conn.close()

        if not row:
            return None
        return {"id": str(row[0]), "title": row[1], "updated_at": row[2].isoformat()}

    @staticmethod
    def delete_chat(chat_id: str, user_id: str) -> bool:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "delete from chats where id = %s and user_id = %s returning id",
                    (chat_id, user_id),
                )
                row = cur.fetchone()
            conn.commit()
        finally:
            conn.close()

        return row is not None

    @staticmethod
    def list_messages(chat_id: str) -> list[dict]:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select id, role, content, image_url, created_at
                    from messages where chat_id = %s order by created_at asc
                    """,
                    (chat_id,),
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        return [
            {
                "id": str(r[0]),
                "role": r[1],
                "content": r[2],
                "image_url": ChatService._resolve_image_url(r[3]),
                "created_at": r[4].isoformat(),
            }
            for r in rows
        ]

    @staticmethod
    def _resolve_image_url(storage_path: str | None) -> str | None:
        """messages.image_url stores a private Storage path — resolve it to a
        short-lived signed URL on read so history stays viewable indefinitely
        (Storage bucket is private, unlike a public CDN link)."""
        if not storage_path:
            return None
        return supabase_storage.create_signed_url(
            storage_path, bucket=CHAT_IMAGES_BUCKET, expires_in=SIGNED_URL_EXPIRES_IN
        )

    @staticmethod
    def upload_chat_image(chat_id: str, filename: str, content: bytes, content_type: str) -> str:
        """Uploads a user-attached image to the private chat-attachments bucket
        and returns the storage path (stored in messages.image_url)."""
        storage_path = f"{chat_id}/{uuid.uuid4()}-{filename}"
        supabase_storage.ensure_bucket_exists(bucket=CHAT_IMAGES_BUCKET)
        supabase_storage.upload_file(storage_path, content, content_type, bucket=CHAT_IMAGES_BUCKET)
        return storage_path

    @staticmethod
    def save_message(chat_id: str, role: str, content: str, image_url: str | None = None) -> dict:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into messages (chat_id, role, content, image_url)
                    values (%s, %s, %s, %s)
                    returning id, role, content, image_url, created_at
                    """,
                    (chat_id, role, content, image_url),
                )
                row = cur.fetchone()
                cur.execute("update chats set updated_at = now() where id = %s", (chat_id,))
            conn.commit()
        finally:
            conn.close()

        return {
            "id": str(row[0]),
            "role": row[1],
            "content": row[2],
            "image_url": row[3],
            "created_at": row[4].isoformat(),
        }

    @staticmethod
    def maybe_set_title_from_first_message(chat_id: str, content: str) -> None:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("select count(*) from messages where chat_id = %s", (chat_id,))
                (message_count,) = cur.fetchone()
                if message_count != 1:
                    return
                cur.execute("select title from chats where id = %s", (chat_id,))
                (title,) = cur.fetchone()
                if title != DEFAULT_TITLE:
                    return
                new_title = content.strip()[:TITLE_MAX_LENGTH] or DEFAULT_TITLE
                cur.execute("update chats set title = %s where id = %s", (new_title, chat_id))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def search_context(query_embedding: list[float]) -> list[str]:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select content from document_chunks
                    order by embedding <=> %s::vector
                    limit %s
                    """,
                    (json.dumps(query_embedding), TOP_K_CHUNKS),
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        return [r[0] for r in rows]


def build_contents(history: list[dict], context_chunks: list[str], user_message: str) -> list[dict]:
    """Builds the Gemini `contents` array: prior turns + a final user turn carrying RAG context."""
    contents = [
        {"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
        for m in history[-HISTORY_LIMIT:]
    ]

    if context_chunks:
        context_block = "\n\n---\n\n".join(context_chunks)
    else:
        context_block = "(sin resultados relevantes en el corpus)"

    final_turn = f"Contexto recuperado del corpus:\n{context_block}\n\nConsulta del usuario: {user_message}"
    contents.append({"role": "user", "parts": [{"text": final_turn}]})
    return contents


def build_vision_messages(
    history: list[dict],
    context_chunks: list[str],
    user_text: str,
    image_base64: str,
    image_media_type: str,
) -> list[dict]:
    """Builds the Anthropic `messages` array for F-04: prior text turns + a final user turn
    carrying the attached image plus whatever RAG context matched the caption text."""
    messages = [
        {"role": "user" if m["role"] == "user" else "assistant", "content": m["content"]}
        for m in history[-HISTORY_LIMIT:]
    ]

    if context_chunks:
        context_block = "\n\n---\n\n".join(context_chunks)
    else:
        context_block = "(sin resultados relevantes en el corpus)"

    final_text = (
        f"Contexto recuperado del corpus:\n{context_block}\n\n"
        f"Consulta del usuario sobre la imagen adjunta: {user_text}"
    )
    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": image_media_type, "data": image_base64},
                },
                {"type": "text", "text": final_text},
            ],
        }
    )
    return messages
