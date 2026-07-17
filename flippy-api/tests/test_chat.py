import io
import uuid

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.integrations import anthropic_vision, gemini, supabase_auth
from main import app

TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000b49444154789c63f80f040009fb03fdfb5e6b2b0000000049454e44ae426082"
)

client = TestClient(app)


@pytest.fixture
def registered_user():
    email = f"sdad-chat-{uuid.uuid4().hex[:12]}@example.com"
    password = "TestPassword123!"
    response = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    yield token
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        supabase_auth.delete_user(payload["sub"])
    except Exception:
        pass


def test_create_chat_requires_auth():
    response = client.post("/api/v1/chats")
    assert response.status_code in (401, 403)


def test_create_and_list_chat(registered_user):
    headers = {"Authorization": f"Bearer {registered_user}"}

    create_response = client.post("/api/v1/chats", headers=headers)
    assert create_response.status_code == 200
    chat = create_response.json()
    assert chat["title"] == "Nuevo chat"

    list_response = client.get("/api/v1/chats", headers=headers)
    assert list_response.status_code == 200
    ids = [c["id"] for c in list_response.json()]
    assert chat["id"] in ids


def test_messages_for_foreign_chat_returns_404(registered_user):
    headers_a = {"Authorization": f"Bearer {registered_user}"}
    chat = client.post("/api/v1/chats", headers=headers_a).json()

    other_email = f"sdad-chat-other-{uuid.uuid4().hex[:12]}@example.com"
    other_password = "TestPassword123!"
    other_result = supabase_auth.sign_up(other_email, other_password)
    headers_b = {"Authorization": f"Bearer {other_result['access_token']}"}

    try:
        response = client.get(f"/api/v1/chats/{chat['id']}/messages", headers=headers_b)
        assert response.status_code == 404
    finally:
        supabase_auth.delete_user(other_result["user"]["id"])


def test_send_message_streams_and_persists(registered_user, monkeypatch):
    def fake_stream_chat(system_prompt, contents):
        yield "Hola "
        yield "mundo"

    monkeypatch.setattr(gemini, "stream_chat", fake_stream_chat)

    headers = {"Authorization": f"Bearer {registered_user}"}
    chat = client.post("/api/v1/chats", headers=headers).json()

    response = client.post(
        f"/api/v1/chats/{chat['id']}/messages",
        headers=headers,
        json={"content": "Que es el ROI?"},
    )
    assert response.status_code == 200
    assert "Hola " in response.text
    assert "mundo" in response.text
    assert "[DONE]" in response.text

    messages = client.get(f"/api/v1/chats/{chat['id']}/messages", headers=headers).json()
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "Que es el ROI?"
    assert messages[1]["content"] == "Hola mundo"

    updated_chat = client.get("/api/v1/chats", headers=headers).json()[0]
    assert updated_chat["title"] == "Que es el ROI?"


def test_rename_chat(registered_user):
    headers = {"Authorization": f"Bearer {registered_user}"}
    chat = client.post("/api/v1/chats", headers=headers).json()

    response = client.patch(
        f"/api/v1/chats/{chat['id']}", headers=headers, json={"title": "Mi chat renombrado"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Mi chat renombrado"

    listed = client.get("/api/v1/chats", headers=headers).json()
    assert listed[0]["title"] == "Mi chat renombrado"


def test_rename_foreign_chat_returns_404(registered_user):
    headers_a = {"Authorization": f"Bearer {registered_user}"}
    chat = client.post("/api/v1/chats", headers=headers_a).json()

    other_email = f"sdad-chat-other-{uuid.uuid4().hex[:12]}@example.com"
    other_password = "TestPassword123!"
    other_result = supabase_auth.sign_up(other_email, other_password)
    headers_b = {"Authorization": f"Bearer {other_result['access_token']}"}

    try:
        response = client.patch(
            f"/api/v1/chats/{chat['id']}", headers=headers_b, json={"title": "Hackeado"}
        )
        assert response.status_code == 404
    finally:
        supabase_auth.delete_user(other_result["user"]["id"])


def test_delete_chat_removes_it_and_its_messages(registered_user, monkeypatch):
    def fake_stream_chat(system_prompt, contents):
        yield "Hola"

    monkeypatch.setattr(gemini, "stream_chat", fake_stream_chat)

    headers = {"Authorization": f"Bearer {registered_user}"}
    chat = client.post("/api/v1/chats", headers=headers).json()
    client.post(f"/api/v1/chats/{chat['id']}/messages", headers=headers, json={"content": "Hola"})

    response = client.delete(f"/api/v1/chats/{chat['id']}", headers=headers)
    assert response.status_code == 204

    ids = [c["id"] for c in client.get("/api/v1/chats", headers=headers).json()]
    assert chat["id"] not in ids

    messages_response = client.get(f"/api/v1/chats/{chat['id']}/messages", headers=headers)
    assert messages_response.status_code == 404


def test_delete_foreign_chat_returns_404(registered_user):
    headers_a = {"Authorization": f"Bearer {registered_user}"}
    chat = client.post("/api/v1/chats", headers=headers_a).json()

    other_email = f"sdad-chat-other-{uuid.uuid4().hex[:12]}@example.com"
    other_password = "TestPassword123!"
    other_result = supabase_auth.sign_up(other_email, other_password)
    headers_b = {"Authorization": f"Bearer {other_result['access_token']}"}

    try:
        response = client.delete(f"/api/v1/chats/{chat['id']}", headers=headers_b)
        assert response.status_code == 404
    finally:
        supabase_auth.delete_user(other_result["user"]["id"])


def test_delete_chat_requires_auth():
    response = client.delete("/api/v1/chats/does-not-matter")
    assert response.status_code in (401, 403)


def test_send_image_message_requires_auth():
    response = client.post(
        "/api/v1/chats/does-not-matter/messages/image",
        files={"file": ("photo.png", io.BytesIO(TINY_PNG), "image/png")},
    )
    assert response.status_code in (401, 403)


def test_send_image_message_for_foreign_chat_returns_404(registered_user):
    headers_a = {"Authorization": f"Bearer {registered_user}"}
    chat = client.post("/api/v1/chats", headers=headers_a).json()

    other_email = f"sdad-chat-other-{uuid.uuid4().hex[:12]}@example.com"
    other_password = "TestPassword123!"
    other_result = supabase_auth.sign_up(other_email, other_password)
    headers_b = {"Authorization": f"Bearer {other_result['access_token']}"}

    try:
        response = client.post(
            f"/api/v1/chats/{chat['id']}/messages/image",
            headers=headers_b,
            files={"file": ("photo.png", io.BytesIO(TINY_PNG), "image/png")},
        )
        assert response.status_code == 404
    finally:
        supabase_auth.delete_user(other_result["user"]["id"])


def test_send_image_message_rejects_non_image_content_type(registered_user):
    headers = {"Authorization": f"Bearer {registered_user}"}
    chat = client.post("/api/v1/chats", headers=headers).json()

    response = client.post(
        f"/api/v1/chats/{chat['id']}/messages/image",
        headers=headers,
        files={"file": ("notes.txt", io.BytesIO(b"hola"), "text/plain")},
    )
    assert response.status_code == 400


def test_send_image_message_rejects_oversized_file(registered_user):
    headers = {"Authorization": f"Bearer {registered_user}"}
    chat = client.post("/api/v1/chats", headers=headers).json()

    oversized = b"\x00" * (5 * 1024 * 1024 + 1)
    response = client.post(
        f"/api/v1/chats/{chat['id']}/messages/image",
        headers=headers,
        files={"file": ("big.png", io.BytesIO(oversized), "image/png")},
    )
    assert response.status_code == 413


def test_send_image_message_streams_and_persists(registered_user, monkeypatch):
    def fake_stream_vision(system_prompt, messages):
        assert messages[-1]["role"] == "user"
        content_blocks = messages[-1]["content"]
        assert content_blocks[0]["type"] == "image"
        assert content_blocks[0]["source"]["media_type"] == "image/png"
        yield "Parece "
        yield "una cocina remodelada"

    monkeypatch.setattr(anthropic_vision, "stream_vision", fake_stream_vision)

    headers = {"Authorization": f"Bearer {registered_user}"}
    chat = client.post("/api/v1/chats", headers=headers).json()

    response = client.post(
        f"/api/v1/chats/{chat['id']}/messages/image",
        headers=headers,
        files={"file": ("cocina.png", io.BytesIO(TINY_PNG), "image/png")},
        data={"content": "¿Qué opinas de esta reforma?"},
    )
    assert response.status_code == 200
    assert "una cocina remodelada" in response.text
    assert "[DONE]" in response.text

    messages = client.get(f"/api/v1/chats/{chat['id']}/messages", headers=headers).json()
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "¿Qué opinas de esta reforma?"
    assert messages[0]["image_url"] is not None
    assert messages[0]["image_url"].startswith("http")
    assert messages[1]["content"] == "Parece una cocina remodelada"

    updated_chat = client.get("/api/v1/chats", headers=headers).json()[0]
    assert updated_chat["title"] == "¿Qué opinas de esta reforma?"
