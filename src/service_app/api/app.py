"""FastAPI application — health check, parse, and WhatsApp webhooks."""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse, Response

from service_app.ingestion import ParseError
from service_app.pricing import parse_transcript
from service_app.schemas import ParseRequest, ParseResponse
from service_app.settings import get_settings
from service_app.whatsapp import meta as meta_whatsapp
from service_app.whatsapp import twilio_handler
from service_app.whatsapp.reply import format_error_reply, format_job_reply

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Service App API",
    description="Phase 1a — parse technician transcripts; WhatsApp demo webhooks.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/parse", response_model=ParseResponse)
def parse_endpoint(body: ParseRequest) -> ParseResponse:
    try:
        return parse_transcript(body.transcript)
    except ParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


async def _meta_reply(sender: str, text: str) -> None:
    settings = get_settings()
    try:
        result = parse_transcript(text)
        reply = format_job_reply(result)
    except ParseError as exc:
        reply = format_error_reply(str(exc))
    except RuntimeError as exc:
        reply = format_error_reply(str(exc))

    await meta_whatsapp.send_text_message(settings, to=sender, body=reply)


@app.get("/webhook/whatsapp")
async def whatsapp_meta_verify(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> PlainTextResponse:
    """Meta Cloud API webhook verification handshake."""
    settings = get_settings()
    if not settings.whatsapp_verify_token:
        raise HTTPException(status_code=503, detail="WHATSAPP_VERIFY_TOKEN is not configured.")

    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return PlainTextResponse(content=hub_challenge or "")

    raise HTTPException(status_code=403, detail="Verification failed.")


@app.post("/webhook/whatsapp")
async def whatsapp_meta_inbound(request: Request) -> dict[str, str]:
    """Receive Meta WhatsApp messages; parse job notes and reply (sync for Cloud Run)."""
    payload: dict[str, Any] = await request.json()
    extracted = meta_whatsapp.extract_inbound_text(payload)
    if extracted is None:
        return {"status": "ignored"}

    sender, text = extracted
    try:
        await _meta_reply(sender, text)
        return {"status": "ok"}
    except Exception:
        logger.exception("Failed to handle Meta WhatsApp message from %s", sender)
        raise HTTPException(status_code=500, detail="Failed to process WhatsApp message.") from None


def _twilio_reply_for_transcript(transcript: str) -> str:
    try:
        result = parse_transcript(transcript)
        return format_job_reply(result)
    except (ParseError, RuntimeError) as exc:
        return format_error_reply(str(exc))


@app.post("/webhook/whatsapp/twilio")
async def whatsapp_twilio_inbound(request: Request) -> Response:
    """
    Twilio WhatsApp sandbox webhook.

    Join the sandbox, point the inbound webhook here, send a job note, get JSON back.
    """
    settings = get_settings()
    form = await request.form()
    transcript = str(form.get("Body", "")).strip()

    if not transcript:
        return Response(
            content=twilio_handler.twiml_message(
                "Send a short job note, e.g. Baker residence, replaced P-trap, 2 hours"
            ),
            media_type="application/xml",
        )

    if settings.twilio_validate_signatures:
        if not settings.twilio_auth_token or not settings.public_base_url:
            raise HTTPException(
                status_code=503,
                detail="TWILIO_AUTH_TOKEN and PUBLIC_BASE_URL required for signature validation.",
            )
        signature = request.headers.get("X-Twilio-Signature", "")
        webhook_url = f"{settings.public_base_url.rstrip('/')}/webhook/whatsapp/twilio"
        params = {k: str(v) for k, v in form.multi_items()}
        if not twilio_handler.validate_twilio_signature(
            settings.twilio_auth_token,
            signature,
            webhook_url,
            params,
        ):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature.")

    reply = _twilio_reply_for_transcript(transcript)
    return Response(content=twilio_handler.twiml_message(reply), media_type="application/xml")
