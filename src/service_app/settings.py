"""Application settings loaded from environment (and optional `.env`)."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration — extend as the product grows."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openrouter_api_key: str | None = Field(
        default=None,
        alias="OPENROUTER_API_KEY",
        description="OpenRouter API key (OpenAI-compatible Chat Completions).",
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_BASE_URL",
    )
    openrouter_http_referer: str | None = Field(
        default=None,
        alias="OPENROUTER_HTTP_REFERER",
    )
    openrouter_x_title: str | None = Field(
        default=None,
        alias="OPENROUTER_X_TITLE",
    )
    openrouter_model: str = Field(
        default="openai/gpt-4o-mini",
        alias="OPENROUTER_MODEL",
    )
    database_url: str | None = Field(
        default=None,
        alias="DATABASE_URL",
        description="SQLAlchemy URL for application data when you enable persistence.",
    )

    # WhatsApp — Meta Cloud API (recommended for Cloud Run webhook URL)
    whatsapp_verify_token: str | None = Field(
        default=None,
        alias="WHATSAPP_VERIFY_TOKEN",
        description="Meta webhook verification token (you choose this string).",
    )
    whatsapp_access_token: str | None = Field(
        default=None,
        alias="WHATSAPP_ACCESS_TOKEN",
        description="Meta Graph API access token for sending WhatsApp messages.",
    )
    whatsapp_phone_number_id: str | None = Field(
        default=None,
        alias="WHATSAPP_PHONE_NUMBER_ID",
        description="Meta WhatsApp phone number ID.",
    )

    # WhatsApp — Twilio sandbox (fastest first demo)
    twilio_auth_token: str | None = Field(
        default=None,
        alias="TWILIO_AUTH_TOKEN",
    )
    twilio_validate_signatures: bool = Field(
        default=True,
        alias="TWILIO_VALIDATE_SIGNATURES",
        description="Validate X-Twilio-Signature on inbound webhooks.",
    )
    public_base_url: str | None = Field(
        default=None,
        alias="PUBLIC_BASE_URL",
        description="Public Cloud Run URL for Twilio signature validation (no trailing slash).",
    )

    web_auth_username: str = Field(default="admin", alias="WEB_AUTH_USERNAME")
    web_auth_password: str | None = Field(
        default=None,
        alias="WEB_AUTH_PASSWORD",
        description="HTTP Basic password for /app web UI (single shop MVP).",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
