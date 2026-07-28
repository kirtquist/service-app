"""QuickBooks Online REST API client."""

from __future__ import annotations

from typing import Any

import httpx

from service_app.qbo.config import QboEnvironment, api_base_url, parse_environment
from service_app.settings import Settings


class QboApiError(Exception):
    """QuickBooks API request failed."""


class QboApiClient:
    """Thin wrapper around the QBO v3 company API."""

    def __init__(
        self,
        settings: Settings,
        *,
        realm_id: str,
        access_token: str,
    ) -> None:
        self._settings = settings
        self.realm_id = realm_id
        self._access_token = access_token
        self._environment = parse_environment(settings.intuit_environment)
        self._base_url = f"{api_base_url(self._environment)}/{realm_id}"

    @property
    def environment(self) -> QboEnvironment:
        return self._environment

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    def get(self, path: str, *, params: dict[str, str] | None = None) -> dict[str, Any]:
        url = f"{self._base_url}/{path.lstrip('/')}"
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=self._headers(), params=params)
        return self._parse_response(response)

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}/{path.lstrip('/')}"
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=self._headers(), json=payload)
        return self._parse_response(response)

    @staticmethod
    def _parse_response(response: httpx.Response) -> dict[str, Any]:
        if response.status_code >= 400:
            raise QboApiError(f"QuickBooks API error ({response.status_code}): {response.text}")
        data = response.json()
        if not isinstance(data, dict):
            raise QboApiError(f"Unexpected QuickBooks API response: {data!r}")
        return data

    def get_company_info(self) -> dict[str, Any]:
        """Verify connectivity — returns CompanyInfo query response."""
        return self.get(f"companyinfo/{self.realm_id}", params={"minorversion": "73"})

    def query(self, sql: str) -> dict[str, Any]:
        return self.get("query", params={"query": sql, "minorversion": "73"})
