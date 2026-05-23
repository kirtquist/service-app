"""Twilio WhatsApp sandbox webhook helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
from urllib.parse import urlencode


def validate_twilio_signature(
    auth_token: str,
    signature: str,
    url: str,
    params: dict[str, str],
) -> bool:
    """Validate X-Twilio-Signature on inbound webhook requests."""
    if not auth_token or not signature:
        return False

    sorted_params = sorted(params.items())
    data = url + urlencode(sorted_params, doseq=True)
    digest = hmac.new(
        auth_token.encode("utf-8"),
        data.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    expected = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(expected, signature)


def twiml_message(body: str) -> str:
    """Return TwiML that replies in WhatsApp with a text message."""
    escaped = (
        body.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{escaped}</Message></Response>'
