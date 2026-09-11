"""Stub forecast client. Frozen contract, no network."""
# ponytail: fake values, real Open-Meteo fetch later


def get_forecast(lat: float, lon: float) -> dict:
    return {
        "temp_c": 28.5,
        "humidity_pct": 65,
        "wind_kph": 12.0,
        "precip_mm": 0.0,
        "condition": "partly_cloudy",
        "source": "stub-openmeteo",
        "lat": lat,
        "lon": lon,
    }


def get_divergence_scenario(forecast: dict | None = None) -> dict:
    return {"spread_c": 0.5, "scenario": "low_spread_stub", "source": "stub"}
