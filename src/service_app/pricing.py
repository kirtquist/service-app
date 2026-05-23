"""Build priced parse responses from validated service-call data."""

from service_app.catalog import PRICE_DATABASE, lookup_item_price
from service_app.ingestion import ParseError, parse_service_call
from service_app.schemas import ParseResponse, ParsedServiceCall, PricedPartLine


def build_parse_response(parsed: ParsedServiceCall) -> ParseResponse:
    """Apply catalog pricing to a validated parse result."""
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


def parse_transcript(transcript: str) -> ParseResponse:
    """Parse a field note and return a priced response."""
    parsed = parse_service_call(transcript)
    return build_parse_response(parsed)


__all__ = ["ParseError", "build_parse_response", "parse_transcript"]
