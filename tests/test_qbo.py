"""Tests for QuickBooks Online OAuth framework and invoice sync."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from service_app.api.app import app
from service_app.db.models import InvoiceStatus, QuickBooksConnection
from service_app.db.session import session_scope
from service_app.invoices import service as invoice_service
from service_app.qbo.invoice_mapping import build_qbo_invoice_payload
from service_app.qbo.oauth import (
    QboTokenSet,
    build_authorization_url,
    create_oauth_state,
    verify_oauth_state,
)
from service_app.qbo.service import _needs_refresh
from service_app.qbo.sync import push_invoice
from service_app.schemas import ParseResponse, PricedPartLine
from service_app.settings import get_settings

SAMPLE_PARSE = ParseResponse(
    customer_name="Baker",
    parts=[PricedPartLine(name="P-trap", quantity=1, unit_price=12.0, line_total=12.0)],
    labor_hours=2.0,
    labor_rate=95.0,
    labor_total=190.0,
    parts_total=12.0,
    estimated_total=202.0,
)


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


def test_quickbooks_callback_trailing_slash_preserves_params(
    client: TestClient,
) -> None:
    settings = get_settings()
    state = create_oauth_state(settings)
    with patch("service_app.web.qbo_routes.exchange_authorization_code") as mock_exchange:
        mock_exchange.return_value = QboTokenSet(
            access_token="access",
            refresh_token="refresh",
            access_token_expires_in=3600,
        )
        response = client.get(
            "/app/integrations/quickbooks/callback/",
            params={"code": "auth-code", "state": state, "realmId": "1234567890"},
            follow_redirects=False,
        )
    assert response.status_code == 303
    assert "connected=1" in response.headers["location"]


def test_quickbooks_callback_surfaces_intuit_error(client: TestClient) -> None:
    response = client.get(
        "/app/integrations/quickbooks/callback",
        params={"error": "access_denied", "error_description": "User declined"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "User%20declined" in response.headers["location"] or "User declined" in response.headers["location"]


def test_needs_refresh_handles_sqlite_naive_expiry() -> None:
    connection = QuickBooksConnection(
        realm_id="1234567890",
        access_token="access",
        refresh_token="refresh",
        access_token_expires_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    assert _needs_refresh(connection) is True


def _seed_approved_invoice() -> int:
    with session_scope() as session:
        invoice = invoice_service.create_invoice_from_parse(
            session,
            SAMPLE_PARSE,
            transcript="Baker job",
            source_channel="test",
        )
        invoice_service.update_invoice_status(session, invoice, InvoiceStatus.APPROVED)
        return invoice.id


def _seed_qbo_connection(session) -> None:
    now = datetime.now(timezone.utc)
    session.add(
        QuickBooksConnection(
            realm_id="1234567890",
            access_token="access",
            refresh_token="refresh",
            access_token_expires_at=now + timedelta(hours=1),
            refresh_token_expires_at=now + timedelta(days=90),
        )
    )
    session.commit()


def test_build_qbo_invoice_payload_includes_labor_and_parts(client: TestClient) -> None:
    with session_scope() as session:
        invoice = invoice_service.create_invoice_from_parse(session, SAMPLE_PARSE)
        payload = build_qbo_invoice_payload(
            invoice,
            customer_id="1",
            service_item_id="2",
        )

    assert payload["DocNumber"] == f"INV-{invoice.id:04d}"
    assert payload["CustomerRef"] == {"value": "1"}
    assert len(payload["Line"]) == 2
    assert payload["Line"][0]["Description"] == "On-site labor"
    assert payload["Line"][1]["Description"] == "P-trap"


@patch("service_app.qbo.sync.get_api_client")
def test_push_invoice_not_connected(mock_get_client: MagicMock, client: TestClient) -> None:
    from service_app.qbo.service import QboNotConnectedError

    mock_get_client.side_effect = QboNotConnectedError("Connect QuickBooks first.")
    invoice_id = _seed_approved_invoice()

    with session_scope() as session:
        invoice = invoice_service.get_invoice(session, invoice_id)
        assert invoice is not None
        result = push_invoice(session, invoice)

    assert result.status == "not_connected"
    assert "Connect QuickBooks" in result.message


@patch("service_app.qbo.sync.get_api_client")
def test_push_invoice_already_synced(mock_get_client: MagicMock, client: TestClient) -> None:
    invoice_id = _seed_approved_invoice()
    with session_scope() as session:
        invoice = invoice_service.get_invoice(session, invoice_id)
        assert invoice is not None
        invoice.qbo_external_id = "999"
        session.commit()
        result = push_invoice(session, invoice)

    assert result.status == "already_synced"
    assert result.external_id == "999"
    mock_get_client.assert_not_called()


@patch("service_app.qbo.sync.get_api_client")
def test_push_invoice_success(mock_get_client: MagicMock, client: TestClient) -> None:
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.query.side_effect = [
        {"QueryResponse": {"Customer": [{"Id": "10"}]}},
        {"QueryResponse": {"Item": [{"Id": "20"}]}},
    ]
    mock_client.create_invoice.return_value = {"Invoice": {"Id": "130"}}

    invoice_id = _seed_approved_invoice()
    with session_scope() as session:
        _seed_qbo_connection(session)
        invoice = invoice_service.get_invoice(session, invoice_id)
        assert invoice is not None
        result = push_invoice(session, invoice)
        refreshed = invoice_service.get_invoice(session, invoice_id)

    assert result.status == "synced"
    assert result.external_id == "130"
    assert refreshed is not None
    assert refreshed.qbo_external_id == "130"
    assert refreshed.qbo_sync_status == "synced"
    assert refreshed.qbo_synced_at is not None
    mock_client.create_invoice.assert_called_once()


@patch("service_app.web.routes.push_invoice")
def test_send_to_quickbooks_web_route(mock_push: MagicMock, client: TestClient) -> None:
    from service_app.qbo.sync import QboSyncResult

    invoice_id = _seed_approved_invoice()
    mock_push.return_value = QboSyncResult(
        status="synced",
        message="Invoice sent to QuickBooks.",
        external_id="130",
    )

    response = client.post(
        f"/app/invoices/{invoice_id}/quickbooks",
        auth=("admin", "testpass"),
        follow_redirects=True,
    )
    mock_push.assert_called_once()
    assert response.status_code == 200
    assert "Invoice sent to QuickBooks" in response.text
    assert "QuickBooks Online" in response.text
