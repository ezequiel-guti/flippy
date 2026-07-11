from app.core.db import get_db_connection
from app.integrations import supabase_auth


class AuthService:
    @staticmethod
    def register(email: str, password: str) -> dict:
        result = supabase_auth.sign_up(email, password)
        user = result["user"]

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into users (id, email)
                    values (%s, %s)
                    on conflict (id) do nothing
                    """,
                    (user["id"], user["email"]),
                )
            conn.commit()
        finally:
            conn.close()

        return {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
        }

    @staticmethod
    def login(email: str, password: str) -> dict:
        result = supabase_auth.sign_in_with_password(email, password)
        return {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
        }

    @staticmethod
    def refresh(refresh_token_value: str) -> dict:
        result = supabase_auth.refresh_token(refresh_token_value)
        return {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
        }

    @staticmethod
    def get_profile(user_id: str) -> dict | None:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "select id, email, plan, status from users where id = %s",
                    (user_id,),
                )
                row = cur.fetchone()
        finally:
            conn.close()

        if not row:
            return None
        return {"id": str(row[0]), "email": row[1], "plan": row[2], "status": row[3]}
