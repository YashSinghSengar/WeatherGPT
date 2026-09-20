"""Canonical location + weather models (B2/B3). Offline, mocked httpx."""
import data.openmeteo_client as OC
from data.canonical import canonical_location, canonical_weather

HOURS = [f"2026-09-11T{h:02d}:00" for h in range(24)] + [f"2026-09-12T{h:02d}:00" for h in range(24)]


def _hourly(full=True):
    hourly = {"time": HOURS}
    for m, vals in (("gfs_seamless", (20.0, 0.0, 80, 10, 2, 5.0)),
                    ("ecmwf_ifs025", (22.0, 0.0, 90, 20, 2, 7.0)),
                    ("icon_seamless", (21.0, 0.0, 85, 30, 61, 6.0))):
        t, r, h, p, c, w = vals
        hourly.update({f"temperature_2m_{m}": [t] * 48, f"rain_{m}": [r] * 48})
        if full:
            hourly.update({f"relative_humidity_2m_{m}": [h] * 48,
                           f"precipitation_probability_{m}": [p] * 48,
                           f"weather_code_{m}": [c] * 48, f"wind_speed_10m_{m}": [w] * 48})
    return hourly


class _Resp:
    def __init__(self, hourly):
        self._h = hourly
    def raise_for_status(self):
        pass
    def json(self):
        return {"hourly": self._h}


def _weather(monkeypatch, full=True):
    monkeypatch.setattr(OC.httpx, "get", lambda *a, **k: _Resp(_hourly(full)))
    monkeypatch.setattr(OC, "_cache_path", lambda lat, lon: OC.Path("/nonexistent-cache.json"))
    return OC.get_canonical_weather(1.0, 2.0)


def test_location_display_name_and_optional_admin():
    loc = canonical_location("Nashik, Maharashtra", 19.99, 73.78, country="India", state="Maharashtra")
    assert loc["display_name"] == "Nashik, Maharashtra" and loc["district"] is None
    assert (loc["latitude"], loc["longitude"]) == (19.99, 73.78)


def test_location_requires_coords():
    for bad in (None,):
        try:
            canonical_location("X", bad, 73.78)
            raise AssertionError("fabricated coords accepted")
        except ValueError:
            pass
        try:
            canonical_location("X", 19.99, bad)
            raise AssertionError("fabricated coords accepted")
        except ValueError:
            pass


def test_provider_converts_to_canonical(monkeypatch):
    w = _weather(monkeypatch)
    assert w["location"] == {"latitude": 1.0, "longitude": 2.0}
    assert w["current"]["temperature"] == 21.0 and w["current"]["timestamp"] in HOURS
    assert len(w["forecast"]) == 2 and all("timestamp" in p for p in w["forecast"])
    assert w["source"]["provider"] == "Open-Meteo" and w["source"]["source"] == "openmeteo"


def test_current_separate_from_forecast(monkeypatch):
    w = _weather(monkeypatch)
    assert set(w) == {"location", "current", "forecast", "source"}
    assert w["forecast"][0]["timestamp"] == "2026-09-11" != w["current"]["timestamp"]
    assert w["current"]["precipitation"] == 0.0  # current-hour rain, not next-day total
    assert w["forecast"][1]["precipitation"] == 0.0


def test_missing_fields_stay_null(monkeypatch):
    w = _weather(monkeypatch, full=False)
    assert w["current"]["humidity"] is None and w["current"]["wind_speed"] is None
    assert w["current"]["weather_code"] is None and w["current"]["feels_like"] is None
    assert w["current"]["wind_direction"] is None
    assert all(p["humidity"] is None and p["weather_code"] is None for p in w["forecast"])


def test_legacy_projection_identical(monkeypatch):
    monkeypatch.setattr(OC.httpx, "get", lambda *a, **k: _Resp(_hourly()))
    monkeypatch.setattr(OC, "_cache_path", lambda lat, lon: OC.Path("/nonexistent-cache.json"))
    w = OC.get_canonical_weather(1.0, 2.0)
    f = OC.to_legacy_forecast(w)
    assert f["temp_c"] == 21.0 and f["humidity_pct"] == 85 and f["precip_prob_pct"] == 20
    assert f["wind_kph"] == round(6.0 * 3.6, 1) and f["weather_code"] == 2
    assert f["condition"] == "partly_cloudy" and f["precip_mm"] == 0.0
    assert (f["lat"], f["lon"]) == (1.0, 2.0) and f["source"] == "openmeteo"


def test_agreement_unchanged_on_canonical():
    from confidence.engine import grade
    from tests.fixtures import PER_NORMAL
    g = grade(PER_NORMAL, {"severity": "green"}, 0.0, 2)
    assert g["grade"] == "A" and g["spread_mm"] == 2.0
    w = canonical_weather(1.0, 2.0, {"temperature": 21.0}, [{"timestamp": "d"}], source="openmeteo")
    assert w["location"] == {"latitude": 1.0, "longitude": 2.0}
