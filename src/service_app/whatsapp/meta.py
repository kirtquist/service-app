"""Meta WhatsApp Cloud API webhook and outbound messages."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from service_app.settings import Settings

logger = logging.getLogger(__name__)

META_GRAPH_URL = "https://graph.facebook.com/v21.0"


def extract_inbound_text(payload: dict[str, Any]) -> tuple[str, str] | None:
    """
    Return (sender_wa_id, message_text) from a Meta webhook payload.

    Ignores delivery receipts and non-text messages.
    """
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            for message in messages:
                if message.get("type") != "text":
                    continue
                text = message.get("text", {}).get("body", "").strip()
                sender = message.get("from", "").strip()
                if sender and text:
                    return sender, text
    return None


async def send_text_message(
    settings: Settings,
    *,
    to: str,
    body: str,
) -> None:
    if not settings.whatsapp_access_token or not settings.whatsapp_phone_number_id:
        raise RuntimeError(
            "WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID must be set for Meta replies."
        )

    url = f"{META_GRAPH_URL}/{settings.whatsapp_phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body[:4096]},
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code >= 400:
            logger.error("Meta WhatsApp send failed: %s %s", response.status_code, response.text)
            response.raise_for_status()
