"""Location independence (B1). Offline: geocoder _search mocked, /ask via fixtures."""
import inspect

import data.geocoder as G
from fastapi.testclient import TestClient

import api.main as M
from tests.fixtures import CITIES, _GENERIC, wire_api

c = TestClient(M.app)

NASHIK = {"name": "Nashik", "latitude": 19.9975, "longitude": 73.7898, "country_code": "IN",
          "country": "India", "admin1": "Maharashtra", "admin2": "Nashik"}
GWALIOR = {"name": "Gwalior", "latitude": 26.2183, "longitude": 78.1828, "country_code": "IN",
           "country": "India", "admin1": "Madhya Pradesh", "admin2": "Gwalior"}
SHIRDI = {"name": "Shirdi", "latitude": 19.7645, "longitude": 74.4762, "country_code": "IN",
          "country": "India", "admin1": "Maharashtra", "admin2": "Ahilyanagar"}

BY_TOKEN = {"nashik": [NASHIK], "gwalior": [GWALIOR], "shirdi": [SHIRDI]}


def _route(place):
    return BY_TOKEN.get((place or "").lower(), [])


def test_a_supported_city_canonical(monkeypatch):
    monkeypatch.setattr(G, "_search", _route)
    canon = G.resolve_canonical("Will it rain tonight in Nashik?")
    assert canon["display_name"] == "Nashik" and canon["latitude"] == 19.9975 and canon["longitude"] == 73.7898
    assert canon["state"] == "Maharashtra" and canon["district"] == "Nashik" and canon["country"] == "India"
    assert canon["source"] == "openmeteo-geocoding"
    assert G.resolve_location("Will it rain tonight in Nashik?")[1:] == (19.9975, 73.7898)


def test_b_unsupported_city_same_pipeline(monkeypatch):
    assert "Gwalior" not in CITIES
    monkeypatch.setattr(G, "_search", _route)
    canon = G.resolve_canonical("Will it rain in Gwalior?")
    assert canon["display_name"] == "Gwalior" and (canon["latitude"], canon["longitude"]) == (26.2183, 78.1828)
    assert canon["state"] == "Madhya Pradesh"


def test_c_small_town_admin_metadata(monkeypatch):
    monkeypatch.setattr(G, "_search", _route)
    canon = G.resolve_canonical("Weather in Shirdi", "Shirdi")
    assert canon["district"] == "Ahilyanagar" and canon["state"] == "Maharashtra"


def test_d_invalid_fails_cleanly(monkeypatch):
    monkeypatch.setattr(G, "_search", lambda place: [])
    assert G.resolve_canonical("xqztwkjvblorp zzzqq") is None
    assert G.resolve_canonical("Weather?", "xqztwkjvblorp") is None
    assert G.geocode("xqztwkjvblorp") is None


def test_d_ask_invalid_no_fabrication(monkeypatch):
    wire_api(monkeypatch)
    monkeypatch.setattr(M, "resolve_canonical", lambda q, loc=None: None)
    d = c.post("/ask", json={"query": "xqztwkjvblorp zzzqq", "language": "en"}).json()
    assert d["location"] is None and d["forecast"] is None and d["advisory"] is None


def test_e_coords_reach_weather_layer(monkeypatch):
    wire_api(monkeypatch)
    seen = {}
    def fake_forecast(lat, lon):
        seen.update(lat=lat, lon=lon)
        return {"temp_c": 25.0, "humidity_pct": 50, "wind_kph": 10.0, "precip_mm": 1.0,
                "precip_prob_pct": 10, "weather_code": 2, "condition": "partly_cloudy",
                "observed_at": "t", "source": "mock", "lat": lat, "lon": lon}
    monkeypatch.setattr(M, "get_forecast", fake_forecast)
    d = c.post("/ask", json={"query": "Will it rain in Gwalior?", "language": "en"}).json()
    assert d["location"]["name"] == "Gwalior"
    assert (seen["lat"], seen["lon"]) == (d["location"]["lat"], d["location"]["lon"]) == _GENERIC
    assert (d["forecast"]["lat"], d["forecast"]["lon"]) == _GENERIC


def test_e_explicit_locality_end_to_end(monkeypatch):
    wire_api(monkeypatch)
    d = c.post("/ask", json={"query": "Will it rain tonight?", "location": "Shirdi", "language": "en"}).json()
    assert d["location"]["name"] == "Shirdi" and d["location"]["district"] == "Shirdi"


def test_f_no_hardcoded_city_dependency():
    import pathlib
    for f in ("api/main.py", "data/geocoder.py", "data/openmeteo_client.py"):
        src = pathlib.Path(f).read_text()
        assert "CITIES" not in src and "SUPPORTED" not in src, f
    sig = inspect.signature(M.get_forecast)
    assert "lat" in sig.parameters and "lon" in sig.parameters
    assert callable(G.resolve_canonical) and callable(G.resolve_location)


def test_stub_path_canonical():
    canon = G.resolve_canonical("nashik_coastal_test")
    assert canon["source"] == "stub" and canon["district"] == "Nashik"
    assert G.geocode("nashik_coastal_test") == (19.9975, 73.7898)
