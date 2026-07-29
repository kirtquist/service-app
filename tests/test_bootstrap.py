"""Tests for database bootstrap and lightweight schema patches."""

import sqlite3

from service_app.db.bootstrap import apply_schema_patches, init_database
from service_app.db.session import get_engine, session_scope
from service_app.invoices import service as invoice_service
from service_app.schemas import ParseResponse, PricedPartLine


def test_apply_schema_patches_adds_qbo_columns(tmp_path) -> None:
    db_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE invoices (
            id INTEGER PRIMARY KEY,
            customer_name TEXT NOT NULL,
            labor_hours REAL NOT NULL DEFAULT 0,
            labor_rate REAL NOT NULL DEFAULT 0,
            labor_total REAL NOT NULL DEFAULT 0,
            parts_total REAL NOT NULL DEFAULT 0,
            estimated_total REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL,
            source_transcript TEXT,
            source_channel TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

    init_database(f"sqlite:///{db_path}")
    engine = get_engine()
    apply_schema_patches(engine)

    conn = sqlite3.connect(db_path)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(invoices)")}
    conn.close()

    assert "qbo_external_id" in columns
    assert "qbo_sync_status" in columns
    assert "qbo_synced_at" in columns

    sample = ParseResponse(
        customer_name="Baker",
        parts=[PricedPartLine(name="P-trap", quantity=1, unit_price=12.0, line_total=12.0)],
        labor_hours=1.0,
        labor_rate=95.0,
        labor_total=95.0,
        parts_total=12.0,
        estimated_total=107.0,
    )
    with session_scope() as session:
        invoice = invoice_service.create_invoice_from_parse(session, sample)
        assert invoice.qbo_external_id is None
