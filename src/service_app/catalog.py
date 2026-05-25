"""
Sample price catalog for plumbing SME demos.

Keys are lowercase. `lookup_item_price()` lowercases the search term.
Include aliases (e.g. "p-trap") alongside long distributor descriptions.
Not every demo prompt part is listed — intentional, to show $0 when unknown.
"""

# Mock database of prices and rates (plumber demo subset)
PRICE_DATABASE: dict[str, float] = {
    "labor_rate": 95.00,  # per hour — adjust per trade/region
    # Kitchen leak prompt — p-trap priced; compression fittings intentionally omitted
    "p-trap": 13.72,
    "charlotte pipe 2 in. abs dwv p-trap w/ solvent weld joint": 13.72,
    # Water heater prompt — expansion tank priced; copper fittings omitted
    "expansion tank": 45.00,
    # Shower valve prompt
    "shower valve cartridge": 28.00,
    # Legacy electrician placeholders (unused in plumber demos)
    "12-2 romex wire": 0.60,
    "single-pole switch": 4.50,
    "pvc valve": 12.00,
    "gfci outlet": 18.00,
}


def lookup_item_price(item_name: str) -> float:
    """Return unit price from the catalog, or 0.0 when unknown."""
    return PRICE_DATABASE.get(item_name.lower(), 0.0)
