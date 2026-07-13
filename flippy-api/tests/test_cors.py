from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_localhost_dev_origin_is_allowed():
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_unknown_origin_is_not_allowed():
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://not-flippy.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in response.headers
