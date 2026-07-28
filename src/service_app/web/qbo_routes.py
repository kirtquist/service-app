"""Web routes for QuickBooks Online OAuth (Phase 3)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from service_app.db.session import get_session
from service_app.qbo.oauth import (
    QboOAuthError,
    build_authorization_url,
    create_oauth_state,
    exchange_authorization_code,
    verify_oauth_state,
)
from service_app.qbo.service import (
    QboConfigurationError,
    disconnect,
    get_active_connection,
    get_api_client,
    require_qbo_configured,
    save_connection_tokens,
)
from service_app.settings import get_settings
from service_app.web.auth import require_web_auth

router = APIRouter(prefix="/app/integrations/quickbooks", tags=["quickbooks"])
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _session_dep() -> Session:
    yield from get_session()


@router.get("", response_class=HTMLResponse, dependencies=[Depends(require_web_auth)])
def quickbooks_settings(
    request: Request,
    session: Session = Depends(_session_dep),
) -> HTMLResponse:
    settings = get_settings()
    connection = get_active_connection(session)
    company_name: str | None = None
    configured = settings.is_qbo_configured()
    connected = connection is not None
    error_message = request.query_params.get("error")
    success_message = request.query_params.get("connected")

    if connected and configured:
        try:
            client = get_api_client(session, settings=settings)
            info = client.get_company_info()
            company_name = info.get("CompanyInfo", {}).get("CompanyName")
        except Exception:
            company_name = connection.realm_id if connection else None

    return templates.TemplateResponse(
        request,
        "quickbooks_settings.html",
        {
            "configured": configured,
            "connected": connected,
            "connection": connection,
            "company_name": company_name,
            "redirect_uri": settings.resolve_intuit_redirect_uri(),
            "environment": settings.intuit_environment,
            "error_message": error_message,
            "success_message": success_message,
        },
    )


@router.get("/connect", dependencies=[Depends(require_web_auth)])
def quickbooks_connect() -> RedirectResponse:
    settings = require_qbo_configured()
    state = create_oauth_state(settings)
    url = build_authorization_url(settings, state=state)
    return RedirectResponse(url=url, status_code=302)


@router.get("/callback")
def quickbooks_callback(
    request: Request,
    session: Session = Depends(_session_dep),
) -> RedirectResponse:
    settings = get_settings()
    params = request.query_params
    code = params.get("code")
    state = params.get("state")
    realm_id = params.get("realmId")
    if not code or not state or not realm_id:
        return RedirectResponse(
            url="/app/integrations/quickbooks?error=Missing+OAuth+parameters+from+Intuit.",
            status_code=303,
        )
    if not verify_oauth_state(settings, state):
        return RedirectResponse(
            url="/app/integrations/quickbooks?error=Invalid+or+expired+OAuth+state.",
            status_code=303,
        )
    try:
        tokens = exchange_authorization_code(settings, code=code)
        save_connection_tokens(session, realm_id=realm_id, tokens=tokens)
    except (QboOAuthError, QboConfigurationError) as exc:
        return RedirectResponse(
            url=f"/app/integrations/quickbooks?error={exc}",
            status_code=303,
        )

    return RedirectResponse(
        url="/app/integrations/quickbooks?connected=1",
        status_code=303,
    )


@router.post("/disconnect", dependencies=[Depends(require_web_auth)])
def quickbooks_disconnect(session: Session = Depends(_session_dep)) -> RedirectResponse:
    disconnect(session)
    return RedirectResponse(url="/app/integrations/quickbooks", status_code=303)
