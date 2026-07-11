import uuid

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.integrations import supabase_auth
from main import app

client = TestClient(app)


@pytest.fixture
def test_user():
    email = f"sdad-test-{uuid.uuid4().hex[:12]}@example.com"
    password = "TestPassword123!"
    yield email, password
    # cleanup: delete the Supabase Auth user created during the test, if any
    try:
        payload = jwt.decode(
            _last_access_token[0],
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        supabase_auth.delete_user(payload["sub"])
    except Exception:
        pass


_last_access_token = [None]


def test_register_login_refresh_me_flow(test_user):
    email, password = test_user

    register_response = client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    assert register_response.status_code == 200
    register_body = register_response.json()
    assert "access_token" in register_body
    assert "refresh_token" in register_body
    _last_access_token[0] = register_body["access_token"]

    login_response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login_response.status_code == 200
    login_body = login_response.json()
    _last_access_token[0] = login_body["access_token"]

    refresh_response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": login_body["refresh_token"]}
    )
    assert refresh_response.status_code == 200
    refresh_body = refresh_response.json()
    _last_access_token[0] = refresh_body["access_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_body['access_token']}"},
    )
    assert me_response.status_code == 200
    me_body = me_response.json()
    assert me_body["email"] == email
    assert me_body["plan"] == "gratuito"
    assert me_body["status"] == "gratuito"


def test_login_with_wrong_password_returns_401(test_user):
    email, password = test_user
    register_response = client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    _last_access_token[0] = register_response.json()["access_token"]

    login_response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "wrong-password"}
    )
    assert login_response.status_code == 401


def test_me_without_token_returns_401():
    response = client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)
