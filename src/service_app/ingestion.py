"""Parse messy technician speech into structured data via OpenRouter."""

import json

from pydantic import ValidationError

from service_app.llm import default_model_id, get_openrouter_client
from service_app.schemas import ParsedServiceCall


class ParseError(ValueError):
    """LLM returned JSON that does not match the expected service-call shape."""


def parse_service_call(transcription: str) -> ParsedServiceCall:
    """
    Use an LLM to extract customer, parts/qty, and labor hours from a log line.

    Returns a validated ParsedServiceCall.
    """
    client = get_openrouter_client()
    model = default_model_id()

    prompt = f"""
    Analyze this service call log from a technician. Extract the customer name,
    any parts used (with quantities), and labor hours.
    Return ONLY a clean JSON object with keys: customer_name, parts (list of {{name, quantity}}),
    labor_hours (number).

    Log: "{transcription}"
    """

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt.strip()}],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Empty response from model")

    try:
        raw = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ParseError(f"Model returned invalid JSON: {exc}") from exc

    try:
        return ParsedServiceCall.model_validate(raw)
    except ValidationError as exc:
        raise ParseError(f"Model JSON failed validation: {exc}") from exc
