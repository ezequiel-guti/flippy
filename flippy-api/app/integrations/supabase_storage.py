"""Thin wrapper over Supabase Storage REST API."""
import httpx

from app.core.config import settings

BUCKET = "documents"


class SupabaseStorageError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def _headers(content_type: str | None = None) -> dict[str, str]:
    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def _raise_for_error(response: httpx.Response) -> None:
    if response.status_code >= 400:
        try:
            detail = response.json().get("message", response.text)
        except Exception:
            detail = response.text
        raise SupabaseStorageError(response.status_code, detail)


def ensure_bucket_exists() -> None:
    response = httpx.get(
        f"{settings.supabase_url}/storage/v1/bucket/{BUCKET}",
        headers=_headers(),
        timeout=10,
    )
    if response.status_code == 200:
        return
    create = httpx.post(
        f"{settings.supabase_url}/storage/v1/bucket",
        headers=_headers("application/json"),
        json={"id": BUCKET, "name": BUCKET, "public": False},
        timeout=10,
    )
    _raise_for_error(create)


def upload_file(path: str, content: bytes, content_type: str) -> None:
    response = httpx.post(
        f"{settings.supabase_url}/storage/v1/object/{BUCKET}/{path}",
        headers=_headers(content_type),
        content=content,
        timeout=30,
    )
    _raise_for_error(response)


def delete_file(path: str) -> None:
    response = httpx.request(
        "DELETE",
        f"{settings.supabase_url}/storage/v1/object/{BUCKET}/{path}",
        headers=_headers("application/json"),
        timeout=10,
    )
    _raise_for_error(response)
