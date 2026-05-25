"""Tests for invoice persistence and approval workflow."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from service_app.api.app import app
from service_app.db.session import session_scope
from service_app.invoices import service as invoice_service
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
    get_settings.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


def test_create_and_approve_invoice(client: TestClient) -> None:
    with session_scope() as session:
        invoice = invoice_service.create_invoice_from_parse(
            session,
            SAMPLE_PARSE,
            transcript="Baker job",
            source_channel="test",
        )
        invoice_id = invoice.id

    response = client.get(
        f"/app/invoices/{invoice_id}",
        auth=("admin", "testpass"),
    )
    assert response.status_code == 200
    assert "Baker" in response.text
    assert "$202.00" in response.text

    response = client.post(
        f"/app/invoices/{invoice_id}/approve",
        auth=("admin", "testpass"),
        follow_redirects=False,
    )
    assert response.status_code == 303

    with session_scope() as session:
        invoice = invoice_service.get_invoice(session, invoice_id)
        assert invoice is not None
        assert invoice.status == "approved"


def test_web_requires_auth(client: TestClient) -> None:
    response = client.get("/app/invoices")
    assert response.status_code == 401


@patch("service_app.web.routes.parse_transcript")
def test_create_invoice_from_web_form(mock_parse, client: TestClient) -> None:
    mock_parse.return_value = SAMPLE_PARSE

    response = client.post(
        "/app/invoices/new",
        data={"transcript": "Smith job, 2 hours"},
        auth=("admin", "testpass"),
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/app/invoices/")

    list_response = client.get("/app/invoices", auth=("admin", "testpass"))
    assert list_response.status_code == 200
    assert "Baker" in list_response.text
