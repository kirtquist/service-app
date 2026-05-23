"""Format priced parse results for WhatsApp chat replies."""

import json

from service_app.schemas import ParseResponse


def format_job_reply(response: ParseResponse) -> str:
    """Human-readable summary plus JSON block for SME demos."""
    lines = [
        f"*Job summary*",
        f"Customer: {response.customer_name}",
        f"Labor: {response.labor_hours}h @ ${response.labor_rate:.2f}/hr = ${response.labor_total:.2f}",
    ]

    if response.parts:
        lines.append("Parts:")
        for part in response.parts:
            lines.append(
                f"  • {part.name} x{part.quantity:g} "
                f"@ ${part.unit_price:.2f} = ${part.line_total:.2f}"
            )
    else:
        lines.append("Parts: (none listed)")

    lines.extend(
        [
            f"Parts total: ${response.parts_total:.2f}",
            f"*Estimated total: ${response.estimated_total:.2f}*",
            "",
            "JSON:",
            json.dumps(response.model_dump(), indent=2),
        ]
    )
    return "\n".join(lines)


def format_error_reply(message: str) -> str:
    return f"Could not parse that job note.\n\n{message}\n\nTry a short note like: Baker residence, replaced P-trap, 2 hours"
