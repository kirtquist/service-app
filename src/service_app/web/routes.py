"""Browser UI for invoice review and approval (Phase 1b)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from service_app.db.models import Invoice, InvoiceStatus
from service_app.db.session import get_session
from service_app.export.csv_export import build_quickbooks_csv, invoice_number
from service_app.export.pdf_export import build_invoice_pdf
from service_app.invoices import service as invoice_service
from service_app.pricing import ParseError, parse_transcript
from service_app.web.auth import require_web_auth

router = APIRouter(prefix="/app", tags=["web"])
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

STATUS_LABELS = {
    InvoiceStatus.DRAFT.value: "Draft",
    InvoiceStatus.PENDING_REVIEW.value: "Pending review",
    InvoiceStatus.APPROVED.value: "Approved",
}


def _session_dep() -> Session:
    yield from get_session()


@router.get("", response_class=RedirectResponse)
def app_root() -> RedirectResponse:
    return RedirectResponse(url="/app/invoices", status_code=302)


@router.get("/logout", response_class=RedirectResponse)
def logout(request: Request) -> RedirectResponse:
    """Clear HTTP Basic credentials in the browser, then show logged-out page."""
    host = request.headers.get("host", "localhost")
    scheme = request.url.scheme
    reset_url = f"{scheme}://logout:logout@{host}/app/logged-out"
    return RedirectResponse(url=reset_url, status_code=302)


@router.get("/logged-out", response_class=HTMLResponse)
def logged_out(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "logged_out.html", {})


@router.get("/invoices", response_class=HTMLResponse, dependencies=[Depends(require_web_auth)])
def invoice_list(
    request: Request,
    status: str | None = None,
    session: Session = Depends(_session_dep),
) -> HTMLResponse:
    invoices = invoice_service.list_invoices(session, status=status)
    return templates.TemplateResponse(
        request,
        "invoice_list.html",
        {
            "invoices": invoices,
            "status_filter": status,
            "status_labels": STATUS_LABELS,
            "statuses": InvoiceStatus,
        },
    )


@router.get("/invoices/new", response_class=HTMLResponse, dependencies=[Depends(require_web_auth)])
def new_invoice_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "invoice_new.html", {})


@router.post("/invoices/new", dependencies=[Depends(require_web_auth)])
def create_invoice_from_transcript(
    transcript: str = Form(...),
    session: Session = Depends(_session_dep),
) -> RedirectResponse:
    try:
        parsed = parse_transcript(transcript.strip())
    except (ParseError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    invoice = invoice_service.create_invoice_from_parse(
        session,
        parsed,
        transcript=transcript.strip(),
        source_channel="web",
    )
    return RedirectResponse(url=f"/app/invoices/{invoice.id}", status_code=303)


@router.get(
    "/invoices/{invoice_id}",
    response_class=HTMLResponse,
    dependencies=[Depends(require_web_auth)],
)
def invoice_detail(
    request: Request,
    invoice_id: int,
    session: Session = Depends(_session_dep),
) -> HTMLResponse:
    invoice = invoice_service.get_invoice(session, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return templates.TemplateResponse(
        request,
        "invoice_detail.html",
        {
            "invoice": invoice,
            "status_labels": STATUS_LABELS,
            "statuses": InvoiceStatus,
        },
    )


@router.post("/invoices/{invoice_id}/approve", dependencies=[Depends(require_web_auth)])
def approve_invoice(
    invoice_id: int,
    session: Session = Depends(_session_dep),
) -> RedirectResponse:
    invoice = invoice_service.get_invoice(session, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice_service.update_invoice_status(session, invoice, InvoiceStatus.APPROVED)
    return RedirectResponse(url=f"/app/invoices/{invoice_id}", status_code=303)


@router.post("/invoices/{invoice_id}/status", dependencies=[Depends(require_web_auth)])
def set_invoice_status(
    invoice_id: int,
    status: str = Form(...),
    session: Session = Depends(_session_dep),
) -> RedirectResponse:
    invoice = invoice_service.get_invoice(session, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")

    try:
        new_status = InvoiceStatus(status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid status") from exc

    invoice_service.update_invoice_status(session, invoice, new_status)
    return RedirectResponse(url=f"/app/invoices/{invoice_id}", status_code=303)


@router.post("/invoices/{invoice_id}/customer", dependencies=[Depends(require_web_auth)])
def update_customer(
    invoice_id: int,
    customer_name: str = Form(...),
    session: Session = Depends(_session_dep),
) -> RedirectResponse:
    invoice = invoice_service.get_invoice(session, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice_service.update_invoice_customer(session, invoice, customer_name)
    return RedirectResponse(url=f"/app/invoices/{invoice_id}", status_code=303)


@router.post("/invoices/{invoice_id}/labor", dependencies=[Depends(require_web_auth)])
def update_labor(
    invoice_id: int,
    labor_hours: float = Form(...),
    labor_rate: float = Form(...),
    session: Session = Depends(_session_dep),
) -> RedirectResponse:
    invoice = invoice_service.get_invoice(session, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice_service.update_invoice_labor(
        session,
        invoice,
        labor_hours=labor_hours,
        labor_rate=labor_rate,
    )
    return RedirectResponse(url=f"/app/invoices/{invoice_id}", status_code=303)


@router.post("/invoices/{invoice_id}/lines/add", dependencies=[Depends(require_web_auth)])
def add_line(
    invoice_id: int,
    name: str = Form(...),
    quantity: float = Form(...),
    unit_price: float = Form(...),
    session: Session = Depends(_session_dep),
) -> RedirectResponse:
    invoice = invoice_service.get_invoice(session, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice_service.add_invoice_line(
        session,
        invoice,
        name=name,
        quantity=quantity,
        unit_price=unit_price,
    )
    return RedirectResponse(url=f"/app/invoices/{invoice_id}", status_code=303)


@router.post(
    "/invoices/{invoice_id}/lines/{line_id}/update",
    dependencies=[Depends(require_web_auth)],
)
def update_line(
    invoice_id: int,
    line_id: int,
    name: str = Form(...),
    quantity: float = Form(...),
    unit_price: float = Form(...),
    session: Session = Depends(_session_dep),
) -> RedirectResponse:
    invoice = invoice_service.get_invoice(session, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")

    try:
        invoice_service.update_invoice_line(
            session,
            invoice,
            line_id,
            name=name,
            quantity=quantity,
            unit_price=unit_price,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return RedirectResponse(url=f"/app/invoices/{invoice_id}", status_code=303)


@router.post(
    "/invoices/{invoice_id}/lines/{line_id}/delete",
    dependencies=[Depends(require_web_auth)],
)
def delete_line(
    invoice_id: int,
    line_id: int,
    session: Session = Depends(_session_dep),
) -> RedirectResponse:
    invoice = invoice_service.get_invoice(session, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")

    try:
        invoice_service.delete_invoice_line(session, invoice, line_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return RedirectResponse(url=f"/app/invoices/{invoice_id}", status_code=303)


def _get_invoice_or_404(session: Session, invoice_id: int) -> Invoice:
    invoice = invoice_service.get_invoice(session, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.get(
    "/invoices/{invoice_id}/export.csv",
    dependencies=[Depends(require_web_auth)],
)
def export_invoice_csv(
    invoice_id: int,
    session: Session = Depends(_session_dep),
) -> Response:
    invoice = _get_invoice_or_404(session, invoice_id)
    if invoice.status != InvoiceStatus.APPROVED.value:
        raise HTTPException(status_code=400, detail="Only approved invoices can be exported.")

    filename = f"{invoice_number(invoice).lower()}-quickbooks.csv"
    return Response(
        content=build_quickbooks_csv(invoice),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/invoices/{invoice_id}/export.pdf",
    dependencies=[Depends(require_web_auth)],
)
def export_invoice_pdf(
    invoice_id: int,
    session: Session = Depends(_session_dep),
) -> Response:
    invoice = _get_invoice_or_404(session, invoice_id)
    if invoice.status != InvoiceStatus.APPROVED.value:
        raise HTTPException(status_code=400, detail="Only approved invoices can be exported.")

    filename = f"{invoice_number(invoice).lower()}.pdf"
    return Response(
        content=build_invoice_pdf(invoice),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
