"""Twilio WhatsApp sandbox webhook helpers."""

from __future__ import annotations

import base64
import hmac
from collections.abc import Mapping, Sequence
from hashlib import sha1
from typing import Any
from urllib.parse import urlparse


def _get_param_values(params: Mapping[str, Any], param_name: str) -> list[str]:
    getlist = getattr(params, "getlist", None)
    if callable(getlist):
        return [str(v) for v in getlist(param_name)]
    value = params.get(param_name)
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    return [str(value)]


def _param_names(params: Mapping[str, Any]) -> set[str]:
    keys = getattr(params, "keys", None)
    if callable(keys):
        return set(keys())
    if hasattr(params, "multi_items"):
        return {k for k, _ in params.multi_items()}
    return set(params.keys())


def compute_twilio_signature(auth_token: str, url: str, params: Mapping[str, Any]) -> str:
    """Compute X-Twilio-Signature using Twilio's documented algorithm."""
    data = url
    for param_name in sorted(_param_names(params)):
        for value in sorted(set(_get_param_values(params, param_name))):
            data += param_name + value

    digest = hmac.new(auth_token.encode("utf-8"), data.encode("utf-8"), sha1).digest()
    return base64.b64encode(digest).decode("utf-8")


def _url_variants(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    without_port = parsed._replace(netloc=parsed.hostname or parsed.netloc).geturl()
    if parsed.port:
        with_port = url
    else:
        port = 443 if parsed.scheme == "https" else 80
        with_port = parsed._replace(netloc=f"{parsed.hostname}:{port}").geturl()
    return without_port, with_port


def validate_twilio_signature(
    auth_token: str,
    signature: str,
    url: str,
    params: Mapping[str, Any],
) -> bool:
    """Validate X-Twilio-Signature on inbound webhook requests."""
    if not auth_token or not signature:
        return False

    for candidate_url in _url_variants(url):
        expected = compute_twilio_signature(auth_token, candidate_url, params)
        if hmac.compare_digest(expected, signature):
            return True
    return False


def twiml_message(body: str) -> str:
    """Return TwiML that replies in WhatsApp with a text message."""
    escaped = (
        body.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{escaped}</Message></Response>'
