"""Persist and refresh QuickBooks Online OAuth connections."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from service_app.db.models import QuickBooksConnection
from service_app.qbo.client import QboApiClient
from service_app.qbo.oauth import QboOAuthError, QboTokenSet, refresh_access_token
from service_app.settings import Settings, get_settings


class QboConfigurationError(Exception):
    """App-level Intuit credentials or redirect URI are missing."""


class QboNotConnectedError(Exception):
    """No QuickBooks company is connected yet."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    """Normalize DB datetimes — SQLite returns naive values for timezone=True columns."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _expires_at(seconds: int) -> datetime:
    return _utcnow() + timedelta(seconds=seconds)


def require_qbo_configured(settings: Settings | None = None) -> Settings:
    settings = settings or get_settings()
    if not settings.is_qbo_configured():
        raise QboConfigurationError(
            "QuickBooks OAuth is not configured. Set INTUIT_CLIENT_ID, INTUIT_CLIENT_SECRET, "
            "and INTUIT_REDIRECT_URI (or PUBLIC_BASE_URL)."
        )
    return settings


def get_active_connection(session: Session) -> QuickBooksConnection | None:
    return session.query(QuickBooksConnection).order_by(QuickBooksConnection.id.desc()).first()


def is_connected(session: Session) -> bool:
    return get_active_connection(session) is not None


def save_connection_tokens(
    session: Session,
    *,
    realm_id: str,
    tokens: QboTokenSet,
) -> QuickBooksConnection:
    now = _utcnow()
    connection = get_active_connection(session)
    if connection is None or connection.realm_id != realm_id:
        if connection is not None and connection.realm_id != realm_id:
            session.delete(connection)
            session.flush()
        connection = QuickBooksConnection(realm_id=realm_id)
        session.add(connection)

    connection.access_token = tokens.access_token
    connection.refresh_token = tokens.refresh_token
    connection.access_token_expires_at = _expires_at(tokens.access_token_expires_in)
    connection.refresh_token_expires_at = (
        _expires_at(tokens.refresh_token_expires_in)
        if tokens.refresh_token_expires_in is not None
        else None
    )
    connection.updated_at = now
    session.commit()
    session.refresh(connection)
    return connection


def _needs_refresh(connection: QuickBooksConnection, *, skew_seconds: int = 120) -> bool:
    expires_at = _as_utc(connection.access_token_expires_at)
    return expires_at <= _utcnow() + timedelta(seconds=skew_seconds)


def refresh_connection_tokens(
    session: Session,
    connection: QuickBooksConnection,
    *,
    settings: Settings | None = None,
) -> QuickBooksConnection:
    settings = require_qbo_configured(settings)
    tokens = refresh_access_token(settings, refresh_token=connection.refresh_token)
    return save_connection_tokens(session, realm_id=connection.realm_id, tokens=tokens)


def get_valid_access_token(
    session: Session,
    *,
    settings: Settings | None = None,
) -> tuple[QuickBooksConnection, str]:
    settings = require_qbo_configured(settings)
    connection = get_active_connection(session)
    if connection is None:
        raise QboNotConnectedError("Connect QuickBooks Online before syncing invoices.")

    if _needs_refresh(connection):
        try:
            connection = refresh_connection_tokens(session, connection, settings=settings)
        except QboOAuthError as exc:
            raise QboNotConnectedError(str(exc)) from exc

    return connection, connection.access_token


def get_api_client(session: Session, *, settings: Settings | None = None) -> QboApiClient:
    settings = require_qbo_configured(settings)
    connection, access_token = get_valid_access_token(session, settings=settings)
    return QboApiClient(settings, realm_id=connection.realm_id, access_token=access_token)


def disconnect(session: Session) -> None:
    connection = get_active_connection(session)
    if connection is None:
        return
    session.delete(connection)
    session.commit()
