import io

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.integrations import supabase_auth
from main import app

client = TestClient(app)


@pytest.fixture
def admin_token():
    email = settings.admin_email_list[0] if settings.admin_email_list else None
    assert email, "ADMIN_EMAILS must be set in .env for these tests"

    password = "TestAdminPass123!"
    try:
        result = supabase_auth.sign_up(email, password)
    except supabase_auth.SupabaseAuthError:
        result = supabase_auth.sign_in_with_password(email, password)

    yield result["access_token"]


@pytest.fixture
def non_admin_token():
    import uuid

    email = f"sdad-nonadmin-{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123!"
    result = supabase_auth.sign_up(email, password)
    yield result["access_token"]
    try:
        payload = jwt.decode(result["access_token"], options={"verify_signature": False})
        supabase_auth.delete_user(payload["sub"])
    except Exception:
        pass


def test_upload_requires_admin(non_admin_token):
    response = client.post(
        "/api/v1/admin/documents",
        headers={"Authorization": f"Bearer {non_admin_token}"},
        files={"file": ("test.txt", io.BytesIO(b"hola mundo"), "text/plain")},
    )
    assert response.status_code == 403


def test_upload_requires_auth():
    response = client.post(
        "/api/v1/admin/documents",
        files={"file": ("test.txt", io.BytesIO(b"hola mundo"), "text/plain")},
    )
    assert response.status_code in (401, 403)


def test_upload_rejects_unsupported_extension(admin_token):
    response = client.post(
        "/api/v1/admin/documents",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("test.exe", io.BytesIO(b"binary"), "application/octet-stream")},
    )
    assert response.status_code == 400


def test_upload_rejects_oversized_file(admin_token):
    oversized = b"x" * (20 * 1024 * 1024 + 1)
    response = client.post(
        "/api/v1/admin/documents",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("big.txt", io.BytesIO(oversized), "text/plain")},
    )
    assert response.status_code == 413


def test_upload_txt_processes_and_lists(admin_token):
    content = b"Este es un documento de prueba sobre requisitos de escritura.\n\nContiene dos parrafos distintos."
    upload_response = client.post(
        "/api/v1/admin/documents",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("requisitos.txt", io.BytesIO(content), "text/plain")},
    )
    assert upload_response.status_code == 200
    doc = upload_response.json()
    assert doc["status"] == "processing"
    doc_id = doc["id"]

    list_response = client.get("/api/v1/admin/documents", headers={"Authorization": f"Bearer {admin_token}"})
    assert list_response.status_code == 200
    docs = list_response.json()
    uploaded = next((d for d in docs if d["id"] == doc_id), None)
    assert uploaded is not None
    assert uploaded["status"] == "ready"
    assert uploaded["chunk_count"] >= 1

    delete_response = client.delete(
        f"/api/v1/admin/documents/{doc_id}", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert delete_response.status_code == 200
