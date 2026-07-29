"""Push approved invoices to QuickBooks Online."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from service_app.db.models import Invoice, InvoiceStatus
from service_app.invoices import service as invoice_service
from service_app.qbo.client import QboApiError
from service_app.qbo.invoice_mapping import (
    build_qbo_invoice_payload,
    find_or_create_customer,
    get_default_service_item_id,
)
from service_app.qbo.service import QboNotConnectedError, get_api_client


@dataclass(frozen=True)
class QboSyncResult:
    status: str
    message: str
    external_id: str | None = None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def push_invoice(session: Session, invoice: Invoice) -> QboSyncResult:
    """Push an approved invoice to QuickBooks Online."""
    if invoice.status != InvoiceStatus.APPROVED.value:
        return QboSyncResult(
            status="error",
            message="Only approved invoices can be sent to QuickBooks.",
        )

    if invoice.qbo_external_id:
        return QboSyncResult(
            status="already_synced",
            message=f"Already synced to QuickBooks (invoice #{invoice.qbo_external_id}).",
            external_id=invoice.qbo_external_id,
        )

    try:
        client = get_api_client(session)
    except QboNotConnectedError as exc:
        return QboSyncResult(status="not_connected", message=str(exc))

    try:
        customer_id = find_or_create_customer(client, invoice.customer_name)
        service_item_id = get_default_service_item_id(client)
        payload = build_qbo_invoice_payload(
            invoice,
            customer_id=customer_id,
            service_item_id=service_item_id,
        )
        response = client.create_invoice(payload)
        external_id = response.get("Invoice", {}).get("Id")
        if not external_id:
            raise QboApiError(f"QuickBooks did not return an invoice Id: {response!r}")

        invoice_service.update_invoice_qbo_sync(
            session,
            invoice,
            external_id=str(external_id),
            sync_status="synced",
            synced_at=_utcnow(),
        )
        return QboSyncResult(
            status="synced",
            message="Invoice sent to QuickBooks.",
            external_id=str(external_id),
        )
    except (QboApiError, ValueError) as exc:
        return QboSyncResult(status="error", message=str(exc))
