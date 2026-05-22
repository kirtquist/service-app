"""
Legacy entrypoint shim — prefer `pip install -e .` and `from service_app import …`.

Demonstrates wired OpenRouter ingestion + catalog lookup.
"""

from service_app.catalog import lookup_item_price, PRICE_DATABASE  # noqa: F401 — public re-exports
from service_app.ingestion import parse_service_call

__all__ = ["lookup_item_price", "parse_service_call", "PRICE_DATABASE"]
