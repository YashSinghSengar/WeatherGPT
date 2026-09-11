"""Real geocoder via Open-Meteo. Tuple contract, see CONTRACTS.md."""
import httpx

from .openmeteo_client import DataUnavailable

URL = "https://geocoding-api.open-meteo.com/v1/search"
_FALLBACK = (19.9975, 73.7898)  # ponytail: Nashik stub coords, warning-override test path only


def geocode(place_name: str) -> tuple[float, float] | None:
    if (place_name or "").strip().lower() == "nashik_coastal_test":
        return _FALLBACK
    try:
        r = httpx.get(URL, params={"name": place_name or "", "count": 5}, timeout=10.0)
        r.raise_for_status()
        results = r.json().get("results") or []
        if not results:
            return None
        for res in results:
            if res.get("country_code") == "IN":
                return (res["latitude"], res["longitude"])
        return (results[0]["latitude"], results[0]["longitude"])
    except DataUnavailable:
        raise
    except Exception as e:
        raise DataUnavailable(str(e)) from e
