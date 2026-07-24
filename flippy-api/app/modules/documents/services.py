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
    def create_document(name: str, doc_type: str, content: bytes, folder_id: str | None = None) -> dict:
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
                    insert into documents (id, name, type, storage_path, status, chunk_count, folder_id)
                    values (%s, %s, %s, %s, 'processing', 0, %s)
                    """,
                    (doc_id, name, doc_type, storage_path, folder_id),
                )
            conn.commit()
        finally:
            conn.close()

        return {"id": doc_id, "name": name, "type": doc_type, "storage_path": storage_path, "folder_id": folder_id}

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
    def list_documents(folder_id: str | None = None, filter_by_folder: bool = False) -> list[dict]:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                query = (
                    "select id, name, type, status, chunk_count, folder_id, created_at "
                    "from documents"
                )
                params: tuple = ()
                if filter_by_folder:
                    if folder_id is None:
                        query += " where folder_id is null"
                    else:
                        query += " where folder_id = %s"
                        params = (folder_id,)
                query += " order by created_at desc"
                cur.execute(query, params)
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
                "folder_id": str(row[5]) if row[5] else None,
                "created_at": row[6].isoformat(),
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

    @staticmethod
    def move_document(doc_id: str, folder_id: str | None) -> dict | None:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    update documents set folder_id = %s where id = %s
                    returning id, name, type, status, chunk_count, folder_id, created_at
                    """,
                    (folder_id, doc_id),
                )
                row = cur.fetchone()
            conn.commit()
        finally:
            conn.close()

        if not row:
            return None
        return {
            "id": str(row[0]),
            "name": row[1],
            "type": row[2],
            "status": row[3],
            "chunk_count": row[4],
            "folder_id": str(row[5]) if row[5] else None,
            "created_at": row[6].isoformat(),
        }


class FoldersService:
    @staticmethod
    def create_folder(name: str, parent_id: str | None) -> dict:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into document_folders (name, parent_id)
                    values (%s, %s)
                    returning id, name, parent_id, created_at, updated_at
                    """,
                    (name, parent_id),
                )
                row = cur.fetchone()
            conn.commit()
        finally:
            conn.close()

        return FoldersService._row_to_dict(row)

    @staticmethod
    def list_folders() -> list[dict]:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "select id, name, parent_id, created_at, updated_at "
                    "from document_folders order by name asc"
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        return [FoldersService._row_to_dict(row) for row in rows]

    @staticmethod
    def update_folder(folder_id: str, name: str | None, parent_id: str | None, move_to_root: bool) -> dict | None:
        """move_to_root distinguishes 'parent_id not sent' (keep as-is) from
        'parent_id explicitly null' (move to root) since both are None otherwise."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                fields = []
                params: list = []
                if name is not None:
                    fields.append("name = %s")
                    params.append(name)
                if move_to_root or parent_id is not None:
                    fields.append("parent_id = %s")
                    params.append(parent_id)
                if not fields:
                    cur.execute(
                        "select id, name, parent_id, created_at, updated_at "
                        "from document_folders where id = %s",
                        (folder_id,),
                    )
                    row = cur.fetchone()
                    return FoldersService._row_to_dict(row) if row else None

                fields.append("updated_at = now()")
                params.append(folder_id)
                cur.execute(
                    f"update document_folders set {', '.join(fields)} where id = %s "
                    "returning id, name, parent_id, created_at, updated_at",
                    params,
                )
                row = cur.fetchone()
            conn.commit()
        finally:
            conn.close()

        return FoldersService._row_to_dict(row) if row else None

    @staticmethod
    def delete_folder(folder_id: str) -> tuple[bool, str | None]:
        """Returns (deleted, error). RN-08: a non-empty folder cannot be deleted."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("select id from document_folders where id = %s", (folder_id,))
                if not cur.fetchone():
                    return False, "not_found"

                cur.execute(
                    "select count(*) from document_folders where parent_id = %s", (folder_id,)
                )
                (subfolder_count,) = cur.fetchone()
                cur.execute("select count(*) from documents where folder_id = %s", (folder_id,))
                (document_count,) = cur.fetchone()
                if subfolder_count > 0 or document_count > 0:
                    return False, "not_empty"

                cur.execute("delete from document_folders where id = %s", (folder_id,))
            conn.commit()
        finally:
            conn.close()

        return True, None

    @staticmethod
    def _row_to_dict(row) -> dict:
        return {
            "id": str(row[0]),
            "name": row[1],
            "parent_id": str(row[2]) if row[2] else None,
            "created_at": row[3].isoformat(),
            "updated_at": row[4].isoformat(),
        }
