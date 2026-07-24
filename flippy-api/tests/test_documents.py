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


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


def test_folder_create_requires_admin(non_admin_token):
    response = client.post(
        "/api/v1/admin/folders",
        headers={"Authorization": f"Bearer {non_admin_token}"},
        json={"name": "Contratos"},
    )
    assert response.status_code == 403


def test_folder_crud_and_nesting(auth_headers):
    parent = client.post("/api/v1/admin/folders", headers=auth_headers, json={"name": "Presupuestos"})
    assert parent.status_code == 200
    parent_id = parent.json()["id"]
    assert parent.json()["parent_id"] is None

    child = client.post(
        "/api/v1/admin/folders",
        headers=auth_headers,
        json={"name": "2026", "parent_id": parent_id},
    )
    assert child.status_code == 200
    child_id = child.json()["id"]
    assert child.json()["parent_id"] == parent_id

    listed = client.get("/api/v1/admin/folders", headers=auth_headers)
    assert listed.status_code == 200
    ids = {f["id"] for f in listed.json()}
    assert {parent_id, child_id} <= ids

    renamed = client.patch(
        f"/api/v1/admin/folders/{child_id}", headers=auth_headers, json={"name": "2026-renombrada"}
    )
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "2026-renombrada"
    assert renamed.json()["parent_id"] == parent_id  # rename-only no debe tocar parent_id

    moved = client.patch(
        f"/api/v1/admin/folders/{child_id}", headers=auth_headers, json={"parent_id": None}
    )
    assert moved.status_code == 200
    assert moved.json()["parent_id"] is None  # movida a raíz

    # la subcarpeta ya se movió a raíz, así que el padre ahora está vacío y puede borrarse
    delete_parent = client.delete(f"/api/v1/admin/folders/{parent_id}", headers=auth_headers)
    assert delete_parent.status_code == 200

    delete_child = client.delete(f"/api/v1/admin/folders/{child_id}", headers=auth_headers)
    assert delete_child.status_code == 200


def test_folder_delete_blocked_when_not_empty(auth_headers):
    folder = client.post("/api/v1/admin/folders", headers=auth_headers, json={"name": "No vacía"})
    folder_id = folder.json()["id"]

    subfolder = client.post(
        "/api/v1/admin/folders", headers=auth_headers, json={"name": "Sub", "parent_id": folder_id}
    )
    subfolder_id = subfolder.json()["id"]

    blocked = client.delete(f"/api/v1/admin/folders/{folder_id}", headers=auth_headers)
    assert blocked.status_code == 409

    # limpieza
    client.delete(f"/api/v1/admin/folders/{subfolder_id}", headers=auth_headers)
    client.delete(f"/api/v1/admin/folders/{folder_id}", headers=auth_headers)


def test_document_can_be_created_in_folder_and_moved(auth_headers):
    folder = client.post("/api/v1/admin/folders", headers=auth_headers, json={"name": "Manuales"})
    folder_id = folder.json()["id"]

    upload = client.post(
        "/api/v1/admin/documents",
        headers=auth_headers,
        data={"folder_id": folder_id},
        files={"file": ("manual.txt", io.BytesIO(b"contenido del manual"), "text/plain")},
    )
    assert upload.status_code == 200
    doc = upload.json()
    assert doc["folder_id"] == folder_id
    doc_id = doc["id"]

    root_listing = client.get("/api/v1/admin/documents", headers=auth_headers)
    assert doc_id not in {d["id"] for d in root_listing.json()}

    folder_listing = client.get(f"/api/v1/admin/documents?folder_id={folder_id}", headers=auth_headers)
    assert doc_id in {d["id"] for d in folder_listing.json()}

    moved = client.patch(
        f"/api/v1/admin/documents/{doc_id}/folder", headers=auth_headers, json={"folder_id": None}
    )
    assert moved.status_code == 200
    assert moved.json()["folder_id"] is None

    # limpieza
    client.delete(f"/api/v1/admin/documents/{doc_id}", headers=auth_headers)
    client.delete(f"/api/v1/admin/folders/{folder_id}", headers=auth_headers)
