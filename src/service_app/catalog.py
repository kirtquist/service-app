"""
Sample price catalog — **electrician-skewed** mock data for development.

Trade focus for this MVP branch is plumbing first; swap keys/values toward
pipes, fittings, and fixture SKUs while keeping the same lookup shape.
"""


# Mock database of prices and rates (electrician placeholders)
PRICE_DATABASE: dict[str, float] = {
    "labor_rate": 95.00,  # per hour — adjust per trade/region
    "12-2 romex wire": 0.60,  # per foot
    "single-pole switch": 4.50,
    "pvc valve": 12.00,  # overlaps with plumbing; useful for demos
    "gfci outlet": 18.00,
}


def lookup_item_price(item_name: str) -> float:
    """Return unit price from the catalog, or 0.0 when unknown."""
    return PRICE_DATABASE.get(item_name.lower(), 0.0)
