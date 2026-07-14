import json
import uuid

from psycopg2.extras import Json

from app.core.db import get_db_connection
from app.integrations import supabase_storage
from app.integrations.openai_embeddings import embed_texts

from .chunking import chunk_text
from .parsers import extract_text

VECTORIZABLE_TYPES = {"pdf", "docx", "txt", "json", "html"}
ALLOWED_TYPES = VECTORIZABLE_TYPES | {"image"}

CONTENT_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
    "json": "application/json",
    "html": "text/html",
    "image": "application/octet-stream",
}


class DocumentsService:
    @staticmethod
    def create_document(name: str, doc_type: str, content: bytes) -> dict:
        if doc_type not in ALLOWED_TYPES:
            raise ValueError(f"Unsupported document type: {doc_type}")

        doc_id = str(uuid.uuid4())
        storage_path = f"{doc_id}/{name}"

        supabase_storage.ensure_bucket_exists()
        supabase_storage.upload_file(storage_path, content, CONTENT_TYPES[doc_type])

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into documents (id, name, type, storage_path, status, chunk_count)
                    values (%s, %s, %s, %s, 'processing', 0)
                    """,
                    (doc_id, name, doc_type, storage_path),
                )
            conn.commit()
        finally:
            conn.close()

        return {"id": doc_id, "name": name, "type": doc_type, "storage_path": storage_path}

    @staticmethod
    def process_document(doc_id: str, content: bytes, doc_type: str) -> None:
        """Runs as a FastAPI background task after the upload response was sent."""
        conn = get_db_connection()
        try:
            if doc_type not in VECTORIZABLE_TYPES:
                # RN-05: las imagenes del corpus no se vectorizan, Claude las procesa en consulta
                with conn.cursor() as cur:
                    cur.execute("update documents set status = 'ready' where id = %s", (doc_id,))
                conn.commit()
                return

            text = extract_text(content, doc_type)
            chunks = chunk_text(text)

            if not chunks:
                with conn.cursor() as cur:
                    cur.execute("update documents set status = 'ready', chunk_count = 0 where id = %s", (doc_id,))
                conn.commit()
                return

            embeddings = embed_texts(chunks)

            with conn.cursor() as cur:
                for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    cur.execute(
                        """
                        insert into document_chunks (document_id, content, embedding, chunk_index, metadata)
                        values (%s, %s, %s::vector, %s, %s)
                        """,
                        (doc_id, chunk, json.dumps(embedding), index, Json({})),
                    )
                cur.execute(
                    "update documents set status = 'ready', chunk_count = %s where id = %s",
                    (len(chunks), doc_id),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            with conn.cursor() as cur:
                cur.execute("update documents set status = 'error' where id = %s", (doc_id,))
            conn.commit()
            raise
        finally:
            conn.close()

    @staticmethod
    def list_documents() -> list[dict]:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "select id, name, type, status, chunk_count, created_at from documents order by created_at desc"
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        return [
            {
                "id": str(row[0]),
                "name": row[1],
                "type": row[2],
                "status": row[3],
                "chunk_count": row[4],
                "created_at": row[5].isoformat(),
            }
            for row in rows
        ]

    @staticmethod
    def delete_document(doc_id: str) -> bool:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("select storage_path from documents where id = %s", (doc_id,))
                row = cur.fetchone()
                if not row:
                    return False
                storage_path = row[0]
                cur.execute("delete from documents where id = %s", (doc_id,))
            conn.commit()
        finally:
            conn.close()

        try:
            supabase_storage.delete_file(storage_path)
        except supabase_storage.SupabaseStorageError:
            pass

        return True
