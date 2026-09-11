"""Stub geocoder. Frozen contract: geocode(place) -> location dict."""
# ponytail: fixed table, real geocoding API later if needed


def geocode(place: str) -> dict:
    name = (place or "").strip() or "Nashik"
    key = name.lower()
    table = {
        "nashik": {"name": "Nashik", "lat": 19.9975, "lon": 73.7898, "state": "Maharashtra", "country": "India"},
        "pune": {"name": "Pune", "lat": 18.5204, "lon": 73.8567, "state": "Maharashtra", "country": "India"},
        "delhi": {"name": "Delhi", "lat": 28.6139, "lon": 77.2090, "state": "Delhi", "country": "India"},
    }
    return table.get(key, {"name": name.title(), "lat": 19.9975, "lon": 73.7898, "state": "Unknown", "country": "India"})
