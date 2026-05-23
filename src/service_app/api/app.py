"""FastAPI application — health check and service-call parsing."""

from fastapi import FastAPI, HTTPException

from service_app.catalog import PRICE_DATABASE, lookup_item_price
from service_app.ingestion import ParseError, parse_service_call
from service_app.schemas import ParseRequest, ParseResponse, PricedPartLine

app = FastAPI(
    title="Service App API",
    description="Phase 1a — parse technician transcripts into structured job data.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/parse", response_model=ParseResponse)
def parse_endpoint(body: ParseRequest) -> ParseResponse:
    try:
        parsed = parse_service_call(body.transcript)
    except ParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    labor_rate = PRICE_DATABASE["labor_rate"]
    priced_parts: list[PricedPartLine] = []
    parts_total = 0.0

    for part in parsed.parts:
        unit_price = lookup_item_price(part.name)
        line_total = round(unit_price * part.quantity, 2)
        parts_total += line_total
        priced_parts.append(
            PricedPartLine(
                name=part.name,
                quantity=part.quantity,
                unit_price=unit_price,
                line_total=line_total,
            )
        )

    labor_total = round(labor_rate * parsed.labor_hours, 2)
    parts_total = round(parts_total, 2)

    return ParseResponse(
        customer_name=parsed.customer_name,
        parts=priced_parts,
        labor_hours=parsed.labor_hours,
        labor_rate=labor_rate,
        labor_total=labor_total,
        parts_total=parts_total,
        estimated_total=round(labor_total + parts_total, 2),
    )
