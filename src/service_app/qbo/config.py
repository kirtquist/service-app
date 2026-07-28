"""Intuit / QuickBooks Online endpoint configuration."""

from __future__ import annotations

from enum import Enum


class QboEnvironment(str, Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"


AUTHORIZATION_ENDPOINT = "https://appcenter.intuit.com/connect/oauth2"
TOKEN_ENDPOINT = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
REVOKE_ENDPOINT = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke"

API_BASE_URLS = {
    QboEnvironment.SANDBOX: "https://sandbox-quickbooks.api.intuit.com/v3/company",
    QboEnvironment.PRODUCTION: "https://quickbooks.api.intuit.com/v3/company",
}

# Minimum scope for reading company info and creating invoices later.
DEFAULT_SCOPES = "com.intuit.quickbooks.accounting"


def parse_environment(value: str) -> QboEnvironment:
    normalized = value.strip().lower()
    if normalized == QboEnvironment.PRODUCTION.value:
        return QboEnvironment.PRODUCTION
    return QboEnvironment.SANDBOX


def api_base_url(environment: QboEnvironment) -> str:
    return API_BASE_URLS[environment]
