"""Export invoices to PDF for customer / office records."""

from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from service_app.db.models import Invoice
from service_app.export.csv_export import invoice_number


def build_invoice_pdf(invoice: Invoice) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - inch

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(inch, y, "Service Invoice")
    y -= 0.35 * inch

    pdf.setFont("Helvetica", 11)
    pdf.drawString(inch, y, f"Invoice: {invoice_number(invoice)}")
    y -= 0.25 * inch
    pdf.drawString(inch, y, f"Customer: {invoice.customer_name}")
    y -= 0.25 * inch
    pdf.drawString(inch, y, f"Date: {invoice.created_at.date().isoformat()}")
    y -= 0.25 * inch
    pdf.drawString(inch, y, f"Status: {invoice.status.replace('_', ' ').title()}")
    y -= 0.45 * inch

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(inch, y, "Line items")
    y -= 0.3 * inch
    pdf.setFont("Helvetica", 10)

    if invoice.lines:
        for line in invoice.lines:
            text = (
                f"• {line.name} — qty {line.quantity:g} @ ${line.unit_price:.2f} "
                f"= ${line.line_total:.2f}"
            )
            pdf.drawString(inch, y, text[:95])
            y -= 0.22 * inch
            if y < inch:
                pdf.showPage()
                y = height - inch
    else:
        pdf.drawString(inch, y, "No parts listed.")
        y -= 0.22 * inch

    y -= 0.15 * inch
    pdf.drawString(
        inch,
        y,
        f"Labor: {invoice.labor_hours:g} hr @ ${invoice.labor_rate:.2f}/hr = ${invoice.labor_total:.2f}",
    )
    y -= 0.35 * inch

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(inch, y, f"Estimated total: ${invoice.estimated_total:.2f}")

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
