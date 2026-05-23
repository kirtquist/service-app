"""Tests for CSV and PDF export."""

from datetime import datetime, timezone

from service_app.db.models import Invoice, InvoiceLine, InvoiceStatus
from service_app.export.csv_export import build_quickbooks_csv, invoice_number
from service_app.export.pdf_export import build_invoice_pdf


def _sample_invoice() -> Invoice:
    invoice = Invoice(
        id=7,
        customer_name="Smith",
        labor_hours=2.0,
        labor_rate=95.0,
        labor_total=190.0,
        parts_total=24.0,
        estimated_total=214.0,
        status=InvoiceStatus.APPROVED.value,
        created_at=datetime(2026, 5, 23, tzinfo=timezone.utc),
    )
    invoice.lines = [
        InvoiceLine(
            id=1,
            invoice_id=7,
            name="P-trap",
            quantity=1,
            unit_price=24.0,
            line_total=24.0,
            sort_order=0,
        )
    ]
    return invoice


def test_invoice_number() -> None:
    assert invoice_number(_sample_invoice()) == "INV-0007"


def test_quickbooks_csv_contains_customer_and_lines() -> None:
    csv_text = build_quickbooks_csv(_sample_invoice())
    assert "Smith" in csv_text
    assert "P-trap" in csv_text
    assert "Labor" in csv_text
    assert "Invoice Number" in csv_text


def test_pdf_export_returns_pdf_bytes() -> None:
    pdf_bytes = build_invoice_pdf(_sample_invoice())
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 100
