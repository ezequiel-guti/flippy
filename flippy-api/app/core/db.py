import psycopg2
from psycopg2.extensions import connection as PGConnection

from app.core.config import settings


def get_db_connection() -> PGConnection:
    return psycopg2.connect(settings.supabase_db_url)
