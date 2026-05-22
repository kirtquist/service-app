"""OpenRouter client — OpenAI SDK with custom base URL and API key from secrets."""

from openai import OpenAI

from service_app.secrets import get_secrets_provider
from service_app.settings import get_settings


def get_openrouter_client() -> OpenAI:
    settings = get_settings()
    secrets = get_secrets_provider()
    headers: dict[str, str] = {}
    if settings.openrouter_http_referer:
        headers["HTTP-Referer"] = settings.openrouter_http_referer
    if settings.openrouter_x_title:
        headers["X-Title"] = settings.openrouter_x_title

    return OpenAI(
        base_url=settings.openrouter_base_url,
        api_key=secrets.get_openrouter_api_key(),
        default_headers=headers or None,
    )


def default_model_id() -> str:
    return get_settings().openrouter_model
