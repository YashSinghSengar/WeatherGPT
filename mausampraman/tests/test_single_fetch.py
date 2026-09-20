import api.main as M
import data.openmeteo_client as OC
from fastapi.testclient import TestClient

c = TestClient(M.app)

PER = {
    "gfs_seamless": {"temp_c": 25.0, "rain_mm": 2.0},
    "ecmwf_ifs025": {"temp_c": 26.0, "rain_mm": 10.0},
    "icon_seamless": {"temp_c": 25.5, "rain_mm": 4.0},
}
FORECAST = {"temp_c": 25.0, "humidity_pct": 0, "wind_kph": 0.0, "precip_mm": 3.0, "condition": "rain", "source": "mock", "lat": 19.99, "lon": 73.78}
GREEN = {"district": "nashik", "severity": "green", "headline": "No warning", "body": "", "issued_at": "d", "capture_date": "d"}


def test_single_prevruns_call_per_request(monkeypatch):
    calls = []
    def fake_prevruns(lat, lon, day):
        calls.append((lat, lon, day))
        return PER
    monkeypatch.setattr(M, "resolve_canonical", lambda q, loc=None: {"display_name": "Nashik", "latitude": 19.99, "longitude": 73.78, "country": "India", "state": "Maharashtra", "district": "Nashik", "source": "fixture"})
    monkeypatch.setattr(M, "get_forecast", lambda lat, lon: FORECAST)
    monkeypatch.setattr(M, "get_warning", lambda d: GREEN)
    monkeypatch.setattr(M, "prevruns_per_model", fake_prevruns)
    d = c.post("/ask", json={"query": "What is the weather in Nashik?"}).json()
    assert len(calls) == 1, calls
    assert d["confidence"]["spread_mm"] == 8.0
    assert d["confidence"]["drivers"] == {"spread_mm": 8.0}
    assert d["confidence"]["grade"] == "B"


def test_scenario_matches_graded_values():
    scen = OC.divergence_scenario_from_models(19.99, 73.78, PER)
    assert scen["precip_mm"] == round((2.0 + 10.0 + 4.0) / 3, 1)
    assert scen["source"] == "openmeteo-prevruns"
