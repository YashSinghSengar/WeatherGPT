"""Stub warning lookup. Frozen contract, no network."""
# ponytail: always none, real IMD feed later


def get_warning(lat: float, lon: float) -> dict:
    return {"level": "none", "headline": "No warning (stub)", "source": "stub-warnings"}
