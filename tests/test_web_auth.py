"""Tests for web UI auth helpers (logout)."""

import pytest
from fastapi.testclient import TestClient

from service_app.api.app import app
from service_app.settings import get_settings


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    monkeypatch.setenv("WEB_AUTH_PASSWORD", "testpass")
    get_settings.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


def test_logout_redirects_to_credential_reset_url(client: TestClient) -> None:
    response = client.get(
        "/app/logout",
        auth=("admin", "testpass"),
        follow_redirects=False,
    )
    assert response.status_code == 302
    location = response.headers["location"]
    assert "/app/logged-out" in location
    assert "logout:logout@" in location


def test_logged_out_page_does_not_require_auth(client: TestClient) -> None:
    response = client.get("/app/logged-out")
    assert response.status_code == 200
    assert "logged out" in response.text.lower()
