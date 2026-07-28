"""Push approved invoices to QuickBooks Online (Phase 3 — stub)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from service_app.db.models import Invoice
from service_app.qbo.service import QboNotConnectedError, get_api_client


@dataclass(frozen=True)
class QboSyncResult:
    status: str
    message: str
    external_id: str | None = None


def push_invoice(session: Session, invoice: Invoice) -> QboSyncResult:
    """
    Push an approved invoice to QuickBooks Online.

    Phase 3 scaffold: verifies connectivity only. Invoice create mapping comes next.
    """
    try:
        client = get_api_client(session)
    except QboNotConnectedError as exc:
        return QboSyncResult(status="not_connected", message=str(exc))

    company = client.get_company_info()
    company_name = (
        company.get("CompanyInfo", {}).get("CompanyName")
        or company.get("QueryResponse", {}).get("CompanyInfo", [{}])[0].get("CompanyName")
        or client.realm_id
    )
    return QboSyncResult(
        status="ready",
        message=f"Connected to QuickBooks company “{company_name}”. Invoice sync not implemented yet.",
    )
