"""Canonical internal models. Dicts, see DECISION #2.

Providers produce data, canonical models represent it, business logic
consumes the models. Missing values stay None, never zero or fabricated.
"""
from datetime import datetime, timezone

LOCATION_SOURCE = "openmeteo-geocoding"
WEATHER_PROVIDER = "Open-Meteo"


def canonical_location(display_name, latitude, longitude, country=None,
                       state=None, district=None, source=LOCATION_SOURCE) -> dict:
    """One location shape. lat/lon mandatory; admin fields best-effort."""
    if latitude is None or longitude is None:
        raise ValueError("canonical location requires latitude and longitude")
    return {
        "display_name": display_name,
        "latitude": latitude,
        "longitude": longitude,
        "country": country,
        "state": state,
        "district": district,
        "source": source or LOCATION_SOURCE,
    }


def canonical_weather(latitude, longitude, current, forecast, source=None,
                      retrieved_at=None, provider=WEATHER_PROVIDER) -> dict:
    """One weather shape: current separate from forecast[]. No fake values."""
    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "current": current,
        "forecast": forecast,
        "source": {
            "provider": provider,
            "source": source or "openmeteo",
            "retrieved_at": retrieved_at or datetime.now(timezone.utc).isoformat(),
        },
    }
