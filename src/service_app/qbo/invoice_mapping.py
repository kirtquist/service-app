"""Map approved invoices to QuickBooks Online Invoice API payloads."""

from __future__ import annotations

from datetime import date
from typing import Any

from service_app.db.models import Invoice
from service_app.export.csv_export import invoice_number
from service_app.qbo.client import QboApiClient, QboApiError


def _escape_qbo_query_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def find_or_create_customer(client: QboApiClient, display_name: str) -> str:
    name = display_name.strip()
    if not name:
        raise ValueError("Customer name is required to create a QuickBooks invoice.")

    escaped = _escape_qbo_query_string(name)
    result = client.query(f"SELECT Id FROM Customer WHERE DisplayName = '{escaped}' MAXRESULTS 1")
    customers = result.get("QueryResponse", {}).get("Customer")
    if customers:
        customer = customers[0] if isinstance(customers, list) else customers
        return str(customer["Id"])

    created = client.create_customer({"DisplayName": name})
    customer_id = created.get("Customer", {}).get("Id")
    if not customer_id:
        raise QboApiError(f"QuickBooks did not return a customer Id: {created!r}")
    return str(customer_id)


def get_default_service_item_id(client: QboApiClient) -> str:
    """Return the Id of a Service item, or any item if none exist."""
    for query in (
        "SELECT Id FROM Item WHERE Type = 'Service' MAXRESULTS 1",
        "SELECT Id FROM Item MAXRESULTS 1",
    ):
        result = client.query(query)
        items = result.get("QueryResponse", {}).get("Item")
        if items:
            item = items[0] if isinstance(items, list) else items
            return str(item["Id"])

    raise QboApiError(
        "No items found in QuickBooks. Create a Service item in your QBO company first."
    )


def build_qbo_invoice_lines(invoice: Invoice, *, service_item_id: str) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []

    if invoice.labor_hours > 0:
        lines.append(
            {
                "DetailType": "SalesItemLineDetail",
                "Amount": round(invoice.labor_total, 2),
                "Description": "On-site labor",
                "SalesItemLineDetail": {
                    "ItemRef": {"value": service_item_id},
                    "Qty": invoice.labor_hours,
                    "UnitPrice": round(invoice.labor_rate, 2),
                },
            }
        )

    for line in invoice.lines:
        lines.append(
            {
                "DetailType": "SalesItemLineDetail",
                "Amount": round(line.line_total, 2),
                "Description": line.name,
                "SalesItemLineDetail": {
                    "ItemRef": {"value": service_item_id},
                    "Qty": line.quantity,
                    "UnitPrice": round(line.unit_price, 2),
                },
            }
        )

    if not lines:
        raise ValueError("Invoice has no line items to send to QuickBooks.")

    return lines


def build_qbo_invoice_payload(
    invoice: Invoice,
    *,
    customer_id: str,
    service_item_id: str,
    invoice_date: date | None = None,
) -> dict[str, Any]:
    when = invoice_date or invoice.created_at.date()
    return {
        "DocNumber": invoice_number(invoice),
        "TxnDate": when.isoformat(),
        "CustomerRef": {"value": customer_id},
        "Line": build_qbo_invoice_lines(invoice, service_item_id=service_item_id),
    }
