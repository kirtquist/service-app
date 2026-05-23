"""Tests for schema validation and API endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from service_app.api.app import app
from service_app.ingestion import ParseError, parse_service_call
from service_app.schemas import ParsedServiceCall, PartLine


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_parsed_service_call_validation() -> None:
    parsed = ParsedServiceCall.model_validate(
        {
            "customer_name": "Baker",
            "parts": [{"name": "GFCI", "quantity": 2}],
            "labor_hours": 1.5,
        }
    )
    assert parsed.customer_name == "Baker"
    assert len(parsed.parts) == 1


def test_parse_endpoint_validation_error() -> None:
    response = client.post("/parse", json={"transcript": ""})
    assert response.status_code == 422


@patch("service_app.api.app.parse_service_call")
def test_parse_endpoint_success(mock_parse: MagicMock) -> None:
    mock_parse.return_value = ParsedServiceCall(
        customer_name="Baker",
        parts=[PartLine(name="gfci outlet", quantity=2)],
        labor_hours=1.5,
    )

    response = client.post(
        "/parse",
        json={"transcript": "Baker job, two GFCIs, 1.5 hours"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["customer_name"] == "Baker"
    assert data["labor_hours"] == 1.5
    assert data["parts"][0]["unit_price"] == 18.0
    assert data["parts"][0]["line_total"] == 36.0
    assert data["labor_total"] == 142.5
    assert data["estimated_total"] == 178.5


@patch("service_app.api.app.parse_service_call")
def test_parse_endpoint_parse_error(mock_parse: MagicMock) -> None:
    mock_parse.side_effect = ParseError("bad shape")

    response = client.post("/parse", json={"transcript": "some log"})
    assert response.status_code == 422
    assert response.json()["detail"] == "bad shape"
