"""Deterministic fixtures. No network. Clearly fake data for offline tests."""
import httpx

CITIES = {
    "Bhopal": (23.26, 77.41),
    "Nashik": (19.99, 73.78),
    "Pune": (18.52, 73.85),
    "Delhi": (28.65, 77.23),
    "Mumbai": (19.07, 72.88),
}

PER_NORMAL = {
    "gfs_seamless": {"temp_c": 25.0, "rain_mm": 2.0},
    "ecmwf_ifs025": {"temp_c": 26.0, "rain_mm": 4.0},
    "icon_seamless": {"temp_c": 25.5, "rain_mm": 3.0},
}
PER_DIVERGENT = {
    "gfs_seamless": {"temp_c": 25.0, "rain_mm": 2.0},
    "ecmwf_ifs025": {"temp_c": 26.0, "rain_mm": 68.0},
    "icon_seamless": {"temp_c": 25.5, "rain_mm": 4.0},
}


def forecast(city="Nashik", temp_c=25.0):
    lat, lon = CITIES[city]
    return {"temp_c": temp_c, "humidity_pct": 50, "wind_kph": 10.0, "precip_mm": 3.0, "precip_prob_pct": 40,
            "weather_code": 61, "condition": "rain", "observed_at": "2026-01-01T00:00",
            "source": "fixture", "lat": lat, "lon": lon}


def warning_green(district="nashik"):
    return {"district": district, "severity": "green", "status": "district_not_covered", "headline": "h",
            "body": "", "issued_at": "d", "capture_date": "d"}


def warning_orange():
    return {"district": "nashik_coastal_test", "severity": "orange", "status": "active_warning",
            "headline": "Heavy rainfall likely", "body": "Stay indoors.", "issued_at": "d", "capture_date": "d"}


def warning_unavailable(district="nashik"):
    return {"district": district, "severity": "green", "status": "warning_data_unavailable",
            "headline": "Warning status unavailable", "body": "", "issued_at": "", "capture_date": ""}


def resolve_fake(city="Nashik"):
    wanted = {city} if city != "*" else set(CITIES)
    def _resolve(query, explicit=None):
        name = (explicit or "").strip()
        if name:
            return ((name,) + CITIES[name]) if name in CITIES else None
        for place, coords in CITIES.items():
            if place in wanted and place.lower() in (query or "").lower():
                return (place,) + coords
        return None
    return _resolve


def wire_api(monkeypatch, city="*", warning="green", divergent=False, daily=None):
    """Patch api.main external calls. warning: green|orange|unavailable."""
    import api.main as M
    w = {"green": warning_green(), "orange": warning_orange(), "unavailable": warning_unavailable()}[warning]
    monkeypatch.setattr(M, "resolve_location", resolve_fake(city))
    monkeypatch.setattr(M, "get_forecast", lambda lat, lon: {**forecast("Nashik"), "lat": lat, "lon": lon})
    monkeypatch.setattr(M, "get_warning", lambda d: w)
    monkeypatch.setattr(M, "prevruns_per_model", lambda lat, lon, day: PER_DIVERGENT if divergent else PER_NORMAL)
    monkeypatch.setattr(M, "get_daily", lambda lat, lon: daily if daily is not None else [])


class _OkResp:
    def __init__(self, text):
        self._t = text
    def raise_for_status(self):
        pass
    def json(self):
        return {"choices": [{"message": {"content": self._t}}]}


def fake_sarvam(monkeypatch, text="ok 1.0"):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _OkResp(text))
