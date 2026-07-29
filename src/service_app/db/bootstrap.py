"""Initialize database engine and schema."""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from service_app.db.base import Base
from service_app.db.session import configure_engine, get_engine

logger = logging.getLogger(__name__)

_INVOICE_QBO_COLUMNS_SQLITE = {
    "qbo_external_id": "VARCHAR(64)",
    "qbo_sync_status": "VARCHAR(32)",
    "qbo_synced_at": "DATETIME",
}

_INVOICE_QBO_COLUMNS_POSTGRES = {
    "qbo_external_id": "VARCHAR(64)",
    "qbo_sync_status": "VARCHAR(32)",
    "qbo_synced_at": "TIMESTAMP WITH TIME ZONE",
}


def resolve_database_url(database_url: str | None) -> str:
    if database_url:
        return database_url
    return "sqlite:///./data/service_app.db"


def _sqlite_column_names(engine: Engine, table: str) -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return {row[1] for row in rows}


def apply_schema_patches(engine: Engine) -> None:
    """Add columns to existing tables when models gain fields (no Alembic yet)."""
    inspector = inspect(engine)
    if not inspector.has_table("invoices"):
        return

    dialect = engine.dialect.name
    if dialect == "sqlite":
        existing = _sqlite_column_names(engine, "invoices")
        columns = _INVOICE_QBO_COLUMNS_SQLITE
        with engine.begin() as conn:
            for name, col_type in columns.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE invoices ADD COLUMN {name} {col_type}"))
                    logger.info("Added column invoices.%s", name)
    elif dialect == "postgresql":
        columns = _INVOICE_QBO_COLUMNS_POSTGRES
        with engine.begin() as conn:
            for name, col_type in columns.items():
                conn.execute(
                    text(f"ALTER TABLE invoices ADD COLUMN IF NOT EXISTS {name} {col_type}")
                )


def init_database(database_url: str | None) -> str:
    """Configure SQLAlchemy and create tables if needed."""
    url = resolve_database_url(database_url)
    if url.startswith("sqlite:///./"):
        db_path = url.removeprefix("sqlite:///./")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    configure_engine(url)
    engine = get_engine()
    Base.metadata.create_all(engine)
    apply_schema_patches(engine)
    logger.info("Database initialized (%s)", url.split("@")[-1])
    return url
