"""Tests for QuickBooks Online OAuth framework."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from service_app.api.app import app
from service_app.qbo.oauth import (
    QboTokenSet,
    build_authorization_url,
    create_oauth_state,
    verify_oauth_state,
)
from service_app.settings import get_settings


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    monkeypatch.setenv("WEB_AUTH_PASSWORD", "testpass")
    monkeypatch.setenv("INTUIT_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("INTUIT_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv(
        "INTUIT_REDIRECT_URI",
        "http://testserver/app/integrations/quickbooks/callback",
    )
    monkeypatch.setenv("INTUIT_ENVIRONMENT", "sandbox")
    get_settings.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


def test_oauth_state_round_trip() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    settings.intuit_client_id = "id"
    settings.intuit_client_secret = "secret"
    settings.intuit_redirect_uri = "http://localhost/callback"

    state = create_oauth_state(settings)
    assert verify_oauth_state(settings, state)


def test_build_authorization_url_contains_client_id() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    settings.intuit_client_id = "my-client"
    settings.intuit_client_secret = "secret"
    settings.intuit_redirect_uri = "http://localhost/callback"

    url = build_authorization_url(settings, state="abc123")
    assert "client_id=my-client" in url
    assert "appcenter.intuit.com" in url


def test_quickbooks_settings_requires_auth(client: TestClient) -> None:
    response = client.get("/app/integrations/quickbooks")
    assert response.status_code == 401


def test_quickbooks_settings_shows_not_connected(client: TestClient) -> None:
    response = client.get("/app/integrations/quickbooks", auth=("admin", "testpass"))
    assert response.status_code == 200
    assert "Not connected" in response.text
    assert "Connect QuickBooks" in response.text


def test_quickbooks_connect_redirects_to_intuit(client: TestClient) -> None:
    response = client.get(
        "/app/integrations/quickbooks/connect",
        auth=("admin", "testpass"),
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "appcenter.intuit.com" in response.headers["location"]


@patch("service_app.web.qbo_routes.exchange_authorization_code")
def test_quickbooks_callback_stores_connection(
    mock_exchange: patch,
    client: TestClient,
) -> None:
    settings = get_settings()
    state = create_oauth_state(settings)
    mock_exchange.return_value = QboTokenSet(
        access_token="access",
        refresh_token="refresh",
        access_token_expires_in=3600,
        refresh_token_expires_in=8726400,
    )

    response = client.get(
        "/app/integrations/quickbooks/callback",
        params={"code": "auth-code", "state": state, "realmId": "1234567890"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "connected=1" in response.headers["location"]

    page = client.get("/app/integrations/quickbooks", auth=("admin", "testpass"))
    assert "Connected" in page.text
    assert "1234567890" in page.text
