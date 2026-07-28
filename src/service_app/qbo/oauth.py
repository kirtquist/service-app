"""Intuit OAuth 2.0 helpers for QuickBooks Online."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx

from service_app.qbo.config import AUTHORIZATION_ENDPOINT, DEFAULT_SCOPES, TOKEN_ENDPOINT
from service_app.settings import Settings


class QboOAuthError(Exception):
    """OAuth handshake or token exchange failed."""


@dataclass(frozen=True)
class QboTokenSet:
    access_token: str
    refresh_token: str
    access_token_expires_in: int
    refresh_token_expires_in: int | None = None
    token_type: str = "bearer"


def _state_secret(settings: Settings) -> str:
    secret = settings.intuit_client_secret
    if not secret:
        raise QboOAuthError("INTUIT_CLIENT_SECRET is not configured.")
    return secret


def create_oauth_state(settings: Settings) -> str:
    """Signed CSRF state for the OAuth redirect (no server-side session store)."""
    payload = {
        "nonce": secrets.token_urlsafe(16),
        "ts": int(time.time()),
    }
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()
    body = body.rstrip("=")
    signature = hmac.new(
        _state_secret(settings).encode(),
        body.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{body}.{signature}"


def verify_oauth_state(settings: Settings, state: str, *, max_age_seconds: int = 600) -> bool:
    if not state or "." not in state:
        return False
    body, signature = state.rsplit(".", 1)
    expected = hmac.new(
        _state_secret(settings).encode(),
        body.encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return False
    padded = body + "=" * (-len(body) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(padded.encode()))
    except (json.JSONDecodeError, ValueError):
        return False
    ts = payload.get("ts")
    if not isinstance(ts, int):
        return False
    return int(time.time()) - ts <= max_age_seconds


def build_authorization_url(settings: Settings, *, state: str) -> str:
    redirect_uri = settings.resolve_intuit_redirect_uri()
    client_id = settings.intuit_client_id
    if not redirect_uri or not client_id:
        raise QboOAuthError(
            "QuickBooks OAuth is not configured. Set INTUIT_CLIENT_ID, INTUIT_CLIENT_SECRET, "
            "and INTUIT_REDIRECT_URI (or PUBLIC_BASE_URL)."
        )
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": DEFAULT_SCOPES,
        "state": state,
    }
    return f"{AUTHORIZATION_ENDPOINT}?{urlencode(params)}"


def _basic_auth_header(client_id: str, client_secret: str) -> str:
    raw = f"{client_id}:{client_secret}".encode()
    return "Basic " + base64.b64encode(raw).decode()


def _parse_token_response(data: dict[str, Any]) -> QboTokenSet:
    try:
        return QboTokenSet(
            access_token=str(data["access_token"]),
            refresh_token=str(data["refresh_token"]),
            access_token_expires_in=int(data["expires_in"]),
            refresh_token_expires_in=(
                int(data["x_refresh_token_expires_in"])
                if data.get("x_refresh_token_expires_in") is not None
                else None
            ),
            token_type=str(data.get("token_type", "bearer")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise QboOAuthError(f"Unexpected token response from Intuit: {data!r}") from exc


def exchange_authorization_code(settings: Settings, *, code: str) -> QboTokenSet:
    redirect_uri = settings.resolve_intuit_redirect_uri()
    client_id = settings.intuit_client_id
    client_secret = settings.intuit_client_secret
    if not redirect_uri or not client_id or not client_secret:
        raise QboOAuthError("QuickBooks OAuth credentials are not configured.")

    headers = {
        "Accept": "application/json",
        "Authorization": _basic_auth_header(client_id, client_secret),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    body = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    with httpx.Client(timeout=30.0) as client:
        response = client.post(TOKEN_ENDPOINT, headers=headers, data=body)
    if response.status_code >= 400:
        raise QboOAuthError(f"Token exchange failed ({response.status_code}): {response.text}")
    return _parse_token_response(response.json())


def refresh_access_token(settings: Settings, *, refresh_token: str) -> QboTokenSet:
    client_id = settings.intuit_client_id
    client_secret = settings.intuit_client_secret
    if not client_id or not client_secret:
        raise QboOAuthError("QuickBooks OAuth credentials are not configured.")

    headers = {
        "Accept": "application/json",
        "Authorization": _basic_auth_header(client_id, client_secret),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    body = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    with httpx.Client(timeout=30.0) as client:
        response = client.post(TOKEN_ENDPOINT, headers=headers, data=body)
    if response.status_code >= 400:
        raise QboOAuthError(f"Token refresh failed ({response.status_code}): {response.text}")
    return _parse_token_response(response.json())
