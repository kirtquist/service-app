"""Invoice CRUD and totals recalculation."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from service_app.db.models import Invoice, InvoiceLine, InvoiceStatus
from service_app.schemas import ParseResponse


def _recalculate_totals(invoice: Invoice) -> None:
    parts_total = round(sum(line.line_total for line in invoice.lines), 2)
    labor_total = round(invoice.labor_hours * invoice.labor_rate, 2)
    invoice.parts_total = parts_total
    invoice.labor_total = labor_total
    invoice.estimated_total = round(parts_total + labor_total, 2)
    invoice.updated_at = datetime.now(timezone.utc)


def create_invoice_from_parse(
    session: Session,
    parsed: ParseResponse,
    *,
    transcript: str | None = None,
    source_channel: str = "api",
    status: InvoiceStatus = InvoiceStatus.PENDING_REVIEW,
) -> Invoice:
    invoice = Invoice(
        customer_name=parsed.customer_name,
        labor_hours=parsed.labor_hours,
        labor_rate=parsed.labor_rate,
        labor_total=parsed.labor_total,
        parts_total=parsed.parts_total,
        estimated_total=parsed.estimated_total,
        status=status.value,
        source_transcript=transcript,
        source_channel=source_channel,
    )
    for index, part in enumerate(parsed.parts):
        invoice.lines.append(
            InvoiceLine(
                name=part.name,
                quantity=part.quantity,
                unit_price=part.unit_price,
                line_total=part.line_total,
                sort_order=index,
            )
        )
    session.add(invoice)
    session.commit()
    session.refresh(invoice)
    return invoice


def list_invoices(session: Session, *, status: str | None = None) -> list[Invoice]:
    stmt = select(Invoice).order_by(Invoice.created_at.desc())
    if status:
        stmt = stmt.where(Invoice.status == status)
    return list(session.scalars(stmt).all())


def get_invoice(session: Session, invoice_id: int) -> Invoice | None:
    return session.get(Invoice, invoice_id)


def update_invoice_line(
    session: Session,
    invoice: Invoice,
    line_id: int,
    *,
    name: str,
    quantity: float,
    unit_price: float,
) -> InvoiceLine:
    line = next((item for item in invoice.lines if item.id == line_id), None)
    if line is None:
        raise ValueError(f"Line {line_id} not found")

    line.name = name.strip()
    line.quantity = quantity
    line.unit_price = unit_price
    line.line_total = round(quantity * unit_price, 2)
    _recalculate_totals(invoice)
    session.commit()
    session.refresh(invoice)
    return line


def add_invoice_line(
    session: Session,
    invoice: Invoice,
    *,
    name: str,
    quantity: float,
    unit_price: float,
) -> InvoiceLine:
    line = InvoiceLine(
        name=name.strip(),
        quantity=quantity,
        unit_price=unit_price,
        line_total=round(quantity * unit_price, 2),
        sort_order=len(invoice.lines),
    )
    invoice.lines.append(line)
    _recalculate_totals(invoice)
    session.commit()
    session.refresh(invoice)
    return line


def delete_invoice_line(session: Session, invoice: Invoice, line_id: int) -> None:
    line = next((item for item in invoice.lines if item.id == line_id), None)
    if line is None:
        raise ValueError(f"Line {line_id} not found")
    invoice.lines.remove(line)
    session.delete(line)
    _recalculate_totals(invoice)
    session.commit()


def update_invoice_status(session: Session, invoice: Invoice, status: InvoiceStatus) -> Invoice:
    invoice.status = status.value
    invoice.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(invoice)
    return invoice


def update_invoice_customer(session: Session, invoice: Invoice, customer_name: str) -> Invoice:
    invoice.customer_name = customer_name.strip()
    invoice.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(invoice)
    return invoice


def update_invoice_labor(
    session: Session,
    invoice: Invoice,
    *,
    labor_hours: float,
    labor_rate: float | None = None,
) -> Invoice:
    invoice.labor_hours = labor_hours
    if labor_rate is not None:
        invoice.labor_rate = labor_rate
    _recalculate_totals(invoice)
    session.commit()
    session.refresh(invoice)
    return invoice
