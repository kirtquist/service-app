"""Tests for WhatsApp webhook handlers and reply formatting."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from service_app.api.app import app
from service_app.schemas import ParseResponse, PricedPartLine
from service_app.settings import Settings
from service_app.whatsapp.meta import extract_inbound_text
from service_app.whatsapp.reply import format_job_reply
from service_app.whatsapp.twilio_handler import compute_twilio_signature, validate_twilio_signature

client = TestClient(app)

SAMPLE_RESPONSE = ParseResponse(
    customer_name="Baker",
    parts=[PricedPartLine(name="P-trap", quantity=1, unit_price=0.0, line_total=0.0)],
    labor_hours=2.0,
    labor_rate=95.0,
    labor_total=190.0,
    parts_total=0.0,
    estimated_total=190.0,
)


def test_format_job_reply_includes_json() -> None:
    text = format_job_reply(SAMPLE_RESPONSE)
    assert "Customer: Baker" in text
    assert "Estimated total: $190.00" in text
    assert '"customer_name": "Baker"' in text


def test_twilio_signature_round_trip() -> None:
    url = "https://service-app-api-fozkmmaapq-uw.a.run.app/webhook/whatsapp/twilio"
    params = {
        "Body": "Baker residence, replaced P-trap, 2 hours",
        "From": "whatsapp:+15644440786",
        "To": "whatsapp:+14155238886",
    }
    auth_token = "test-auth-token"
    signature = compute_twilio_signature(auth_token, url, params)
    assert validate_twilio_signature(auth_token, signature, url, params)
    assert not validate_twilio_signature(auth_token, signature, url + "/", params)


def test_extract_inbound_text() -> None:
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "15551234567",
                                    "type": "text",
                                    "text": {"body": "Baker job, 2 hours"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    assert extract_inbound_text(payload) == ("15551234567", "Baker job, 2 hours")


@patch("service_app.api.app.get_settings")
def test_meta_webhook_verify(mock_settings: MagicMock) -> None:
    mock_settings.return_value = Settings(
        WHATSAPP_VERIFY_TOKEN="test-verify-token",
    )
    response = client.get(
        "/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test-verify-token",
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 200
    assert response.text == "12345"


@patch("service_app.api.app.get_settings")
def test_meta_webhook_verify_rejects_bad_token(mock_settings: MagicMock) -> None:
    mock_settings.return_value = Settings(WHATSAPP_VERIFY_TOKEN="expected")
    response = client.get(
        "/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong",
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 403


@patch("service_app.api.app.meta_whatsapp.send_text_message", new_callable=AsyncMock)
@patch("service_app.api.app.parse_transcript")
@patch("service_app.api.app.get_settings")
def test_meta_webhook_inbound(
    mock_settings: MagicMock,
    mock_parse: MagicMock,
    mock_send: AsyncMock,
) -> None:
    mock_settings.return_value = Settings(
        WHATSAPP_ACCESS_TOKEN="token",
        WHATSAPP_PHONE_NUMBER_ID="123456",
    )
    mock_parse.return_value = SAMPLE_RESPONSE

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "15551234567",
                                    "type": "text",
                                    "text": {"body": "Baker job, 2 hours"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    response = client.post("/webhook/whatsapp", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    mock_send.assert_awaited_once()


@patch("service_app.api.app.parse_transcript")
@patch("service_app.api.app.get_settings")
def test_twilio_webhook_with_signature_check(
    mock_settings: MagicMock,
    mock_parse: MagicMock,
) -> None:
    mock_settings.return_value = Settings(
        TWILIO_VALIDATE_SIGNATURES=True,
        TWILIO_AUTH_TOKEN="12345",
        PUBLIC_BASE_URL="https://example.com",
    )
    mock_parse.return_value = SAMPLE_RESPONSE

    url = "https://example.com/webhook/whatsapp/twilio"
    params = {
        "Body": "Baker job, 2 hours",
        "From": "whatsapp:+15551234567",
    }
    signature = compute_twilio_signature("12345", url, params)

    response = client.post(
        "/webhook/whatsapp/twilio",
        data=params,
        headers={"X-Twilio-Signature": signature},
    )
    assert response.status_code == 200
    assert "Customer: Baker" in response.text


@patch("service_app.api.app.parse_transcript")
@patch("service_app.api.app.get_settings")
def test_twilio_webhook_without_signature_check(
    mock_settings: MagicMock,
    mock_parse: MagicMock,
) -> None:
    mock_settings.return_value = Settings(TWILIO_VALIDATE_SIGNATURES=False)
    mock_parse.return_value = SAMPLE_RESPONSE

    response = client.post(
        "/webhook/whatsapp/twilio",
        data={"Body": "Baker job, 2 hours", "From": "whatsapp:+15551234567"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert "Customer: Baker" in response.text
