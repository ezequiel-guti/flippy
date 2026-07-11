"""Thin wrapper over Supabase Auth (GoTrue) REST API.

Server-side calls use the service_role key as the `apikey` header. Supabase Auth
owns password hashing, refresh token rotation, and credential storage — no
password ever touches flippy-api's own database.
"""
import httpx

from app.core.config import settings


class SupabaseAuthError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def _auth_url(path: str) -> str:
    return f"{settings.supabase_url}/auth/v1{path}"


def _headers() -> dict[str, str]:
    return {
        "apikey": settings.supabase_service_role_key,
        "Content-Type": "application/json",
    }


def _raise_for_error(response: httpx.Response) -> None:
    if response.status_code >= 400:
        detail = response.json().get("error_description") or response.json().get("msg") or response.text
        raise SupabaseAuthError(response.status_code, detail)


def sign_up(email: str, password: str) -> dict:
    response = httpx.post(
        _auth_url("/signup"),
        headers=_headers(),
        json={"email": email, "password": password},
        timeout=10,
    )
    _raise_for_error(response)
    return response.json()


def sign_in_with_password(email: str, password: str) -> dict:
    response = httpx.post(
        _auth_url("/token?grant_type=password"),
        headers=_headers(),
        json={"email": email, "password": password},
        timeout=10,
    )
    _raise_for_error(response)
    return response.json()


def refresh_token(refresh_token_value: str) -> dict:
    response = httpx.post(
        _auth_url("/token?grant_type=refresh_token"),
        headers=_headers(),
        json={"refresh_token": refresh_token_value},
        timeout=10,
    )
    _raise_for_error(response)
    return response.json()


def delete_user(user_id: str) -> None:
    """Admin-only. Used in tests to clean up users created during the run."""
    response = httpx.delete(
        _auth_url(f"/admin/users/{user_id}"),
        headers=_headers(),
        timeout=10,
    )
    _raise_for_error(response)
