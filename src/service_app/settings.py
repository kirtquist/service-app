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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
