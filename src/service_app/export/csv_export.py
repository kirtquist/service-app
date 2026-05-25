"""Export invoices to QuickBooks-friendly CSV."""

from __future__ import annotations

import csv
import io
from datetime import date

from service_app.db.models import Invoice


def invoice_number(invoice: Invoice) -> str:
    return f"INV-{invoice.id:04d}"


def build_quickbooks_csv(invoice: Invoice, *, invoice_date: date | None = None) -> str:
    """
    Build a CSV suitable for QuickBooks Online manual import / bookkeeper handoff.

    One row per line item; labor appears as its own row when hours > 0.
    """
    when = invoice_date or invoice.created_at.date()
    date_str = when.isoformat()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Invoice Number",
            "Customer",
            "Invoice Date",
            "Product/Service",
            "Description",
            "Quantity",
            "Rate",
            "Amount",
        ]
    )

    inv_no = invoice_number(invoice)

    if invoice.labor_hours > 0:
        writer.writerow(
            [
                inv_no,
                invoice.customer_name,
                date_str,
                "Labor",
                "On-site labor",
                f"{invoice.labor_hours:g}",
                f"{invoice.labor_rate:.2f}",
                f"{invoice.labor_total:.2f}",
            ]
        )

    for line in invoice.lines:
        writer.writerow(
            [
                inv_no,
                invoice.customer_name,
                date_str,
                "Parts",
                line.name,
                f"{line.quantity:g}",
                f"{line.unit_price:.2f}",
                f"{line.line_total:.2f}",
            ]
        )

    return output.getvalue()
