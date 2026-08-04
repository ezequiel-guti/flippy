"""Reprocesa todos los documentos en estado 'ready' (o 'error') con el pipeline
RAG vigente — necesario una vez, después de introducir chunking por estrategia
y metadatos tipados (SPEC_RAG.md), para que el corpus ingerido con el pipeline
viejo (tipo/fecha_vigencia/region = NULL) quede con metadatos reales.

Llamadas reales a Storage + OpenAI embeddings + Gemini (costo ~USD 1-2 para
el corpus actual, SPEC_RAG.md §5.5). Uso: python scripts/reprocess_all_ready.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from app.core.db import get_db_connection
from app.modules.documents.services import DocumentsService


def main() -> None:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("select id, name from documents where status in ('ready', 'error') order by created_at")
            rows = cur.fetchall()
    finally:
        conn.close()

    print(f"Reprocesando {len(rows)} documentos...")
    for doc_id, name in rows:
        doc_id = str(doc_id)
        try:
            prepared = DocumentsService.prepare_reprocess(doc_id)
            if not prepared:
                print(f"  SKIP {name} — no encontrado")
                continue
            DocumentsService.process_document(doc_id, prepared["content"], prepared["type"], prepared["name"])
            print(f"  OK   {name}")
        except Exception as exc:
            print(f"  FAIL {name} — {exc}")


if __name__ == "__main__":
    main()
