"""
API key resolution for OpenRouter.

MVP: keys come from environment (via pydantic-settings / `.env`).

For production, inject the same variables from your platform's secret manager
rather than committing values or storing raw keys in the application database.
"""


from typing import Protocol

from service_app.settings import Settings, get_settings


class SecretsProvider(Protocol):
    """Pluggable secrets — swap EnvSecretsProvider for a Vault-backed one later."""

    def get_openrouter_api_key(self) -> str: ...


class EnvSecretsProvider:
    """Reads OPENROUTER_API_KEY from configured Settings (env + optional `.env`)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def get_openrouter_api_key(self) -> str:
        key = self._settings.openrouter_api_key
        if not key or not key.strip():
            raise RuntimeError(
                "OPENROUTER_API_KEY is missing. Copy `.env.example` to `.env` and set the key, "
                "or export it in your environment / CI secrets. See docs/API_KEYS.md."
            )
        return key.strip()


_default_provider: SecretsProvider | None = None


def get_secrets_provider() -> SecretsProvider:
    global _default_provider
    if _default_provider is None:
        _default_provider = EnvSecretsProvider()
    return _default_provider


def set_secrets_provider(provider: SecretsProvider) -> None:
    """Used in tests or when wiring a Vault-backed implementation."""
    global _default_provider
    _default_provider = provider
