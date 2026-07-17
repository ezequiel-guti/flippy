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


def ensure_bucket_exists(bucket: str = BUCKET) -> None:
    response = httpx.get(
        f"{settings.supabase_url}/storage/v1/bucket/{bucket}",
        headers=_headers(),
        timeout=10,
    )
    if response.status_code == 200:
        return
    create = httpx.post(
        f"{settings.supabase_url}/storage/v1/bucket",
        headers=_headers("application/json"),
        json={"id": bucket, "name": bucket, "public": False},
        timeout=10,
    )
    _raise_for_error(create)


def upload_file(path: str, content: bytes, content_type: str, bucket: str = BUCKET) -> None:
    response = httpx.post(
        f"{settings.supabase_url}/storage/v1/object/{bucket}/{path}",
        headers=_headers(content_type),
        content=content,
        timeout=30,
    )
    _raise_for_error(response)


def delete_file(path: str, bucket: str = BUCKET) -> None:
    response = httpx.request(
        "DELETE",
        f"{settings.supabase_url}/storage/v1/object/{bucket}/{path}",
        headers=_headers("application/json"),
        timeout=10,
    )
    _raise_for_error(response)


def create_signed_url(path: str, bucket: str = BUCKET, expires_in: int = 3600) -> str:
    """Returns a temporary public URL for a file in a private bucket."""
    response = httpx.post(
        f"{settings.supabase_url}/storage/v1/object/sign/{bucket}/{path}",
        headers=_headers("application/json"),
        json={"expiresIn": expires_in},
        timeout=10,
    )
    _raise_for_error(response)
    signed_path = response.json()["signedURL"]
    return f"{settings.supabase_url}/storage/v1{signed_path}"
