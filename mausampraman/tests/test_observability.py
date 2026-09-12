import logging

import api.main as M
from data.openmeteo_client import DataUnavailable
from fastapi.testclient import TestClient

c = TestClient(M.app)

FORECAST = {"temp_c": 25.0, "humidity_pct": 50, "wind_kph": 10.0, "precip_mm": 3.0, "precip_prob_pct": 40,
            "weather_code": 61, "condition": "rain", "observed_at": "t", "source": "mock", "lat": 19.99, "lon": 73.78}
GREEN = {"district": "n", "severity": "green", "status": "district_not_covered", "headline": "h", "body": "", "issued_at": "d", "capture_date": "d"}
PER = {"gfs_seamless": {"temp_c": 25.0, "rain_mm": 2.0}, "ecmwf_ifs025": {"temp_c": 26.0, "rain_mm": 4.0}, "icon_seamless": {"temp_c": 25.5, "rain_mm": 3.0}}


def _wire(monkeypatch):
    monkeypatch.setattr(M, "resolve_location", lambda q, loc=None: ("Nashik", 19.99, 73.78))
    monkeypatch.setattr(M, "get_forecast", lambda lat, lon: FORECAST)
    monkeypatch.setattr(M, "get_warning", lambda d: GREEN)
    monkeypatch.setattr(M, "prevruns_per_model", lambda lat, lon, day: PER)
    monkeypatch.setattr(M, "get_daily", lambda lat, lon: [])


def test_request_id_unique_and_logged(monkeypatch, caplog):
    _wire(monkeypatch)
    with caplog.at_level(logging.INFO, logger="mausampraman"):
        r1 = c.post("/ask", json={"query": "Weather in Nashik?"})
        r2 = c.post("/ask", json={"query": "Weather in Nashik?"})
    h1, h2 = r1.headers.get("X-Request-ID"), r2.headers.get("X-Request-ID")
    assert h1 and h2 and h1 != h2
    recs = [r for r in caplog.records if r.name == "mausampraman"]
    assert recs and all("SARVAM_API_KEY" not in r.getMessage() and "Bearer" not in r.getMessage() for r in recs)
    import json
    last = json.loads(recs[-1].getMessage())
    assert last["intent"] == "weather_current" and last["grade"] == "A" and last["duration_ms"] >= 0


def test_failure_logged_with_category(monkeypatch, caplog):
    _wire(monkeypatch)
    def boom(lat, lon):
        raise DataUnavailable("meteo down")
    monkeypatch.setattr(M, "get_forecast", boom)
    with caplog.at_level(logging.INFO, logger="mausampraman"):
        r = c.post("/ask", json={"query": "Weather in Nashik?"})
    assert r.status_code == 503 and r.headers.get("X-Request-ID")
    import json
    recs = [r for r in caplog.records if r.name == "mausampraman"]
    assert recs and json.loads(recs[-1].getMessage())["upstream_failure"] == "forecast"
