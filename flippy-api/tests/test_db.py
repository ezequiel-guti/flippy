from app.core.db import get_db_connection


def test_db_connection_reaches_supabase():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("select 1")
            assert cur.fetchone() == (1,)
    finally:
        conn.close()


def test_expected_tables_exist():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "select table_name from information_schema.tables where table_schema = 'public'"
            )
            tables = {row[0] for row in cur.fetchall()}
        expected = {"users", "chats", "messages", "documents", "document_chunks", "subscriptions"}
        assert expected.issubset(tables)
    finally:
        conn.close()
