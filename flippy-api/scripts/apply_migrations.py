"""Apply SQL migration files in supabase/migrations, in filename order.

Usage: python scripts/apply_migrations.py
Requires SUPABASE_DB_URL in .env (direct connection, not the transaction pooler).
"""
import pathlib
import sys

import psycopg2
from dotenv import dotenv_values

MIGRATIONS_DIR = pathlib.Path(__file__).parent.parent / "supabase" / "migrations"


def main() -> None:
    env = dotenv_values(pathlib.Path(__file__).parent.parent / ".env")
    db_url = env.get("SUPABASE_DB_URL")
    if not db_url:
        print("SUPABASE_DB_URL is not set in .env", file=sys.stderr)
        sys.exit(1)

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        print("No migration files found in", MIGRATIONS_DIR, file=sys.stderr)
        sys.exit(1)

    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            for path in migration_files:
                print(f"Applying {path.name}...")
                cur.execute(path.read_text(encoding="utf-8"))
        print(f"Applied {len(migration_files)} migration file(s) successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
