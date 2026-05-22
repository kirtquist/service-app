"""Parse messy technician speech into structured data via OpenRouter."""

import json

from service_app.llm import default_model_id, get_openrouter_client


def parse_service_call(transcription: str) -> dict:
    """
    Use an LLM to extract customer, parts/qty, and labor hours from a log line.

    Returns a dict parsed from JSON returned by the model.
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
    return json.loads(content)
