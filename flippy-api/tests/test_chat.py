import uuid

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.integrations import gemini, supabase_auth
from main import app

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
