"""Provider boundary (B4/B5). Coords in, canonical out, errors structured. Offline."""
import json

import api.main as M
import data.openmeteo_client as OC
from data.provider import OpenMeteoProvider, provider
from fastapi.testclient import TestClient
from tests.fixtures import wire_api

c = TestClient(M.app)
HOURS = [f"2026-09-11T{h:02d}:00" for h in range(24)] + [f"2026-09-12T{h:02d}:00" for h in range(24)]


def _hourly():
    hourly = {"time": HOURS}
    for m in ("gfs_seamless", "ecmwf_ifs025", "icon_seamless"):
        hourly.update({f"temperature_2m_{m}": [20.0] * 48, f"rain_{m}": [1.0] * 48,
                       f"relative_humidity_2m_{m}": [80] * 48,
                       f"precipitation_probability_{m}": [10] * 48,
                       f"weather_code_{m}": [2] * 48, f"wind_speed_10m_{m}": [5.0] * 48})
    return hourly


class _Resp:
    def __init__(self, hourly):
        self._h = hourly
    def raise_for_status(self):
        pass
    def json(self):
        return {"hourly": self._h}


def test_coords_reach_adapter(monkeypatch):
    seen = {}
    def fake_get(url, params=None, timeout=None):
        seen.update(url=url, params=params)
        return _Resp(_hourly())
    monkeypatch.setattr(OC.httpx, "get", fake_get)
    monkeypatch.setattr(OC, "_cache_path", lambda lat, lon: OC.Path("/nonexistent-cache.json"))
    w = provider.get_canonical(19.99, 73.78)
    assert seen["params"]["latitude"] == 19.99 and seen["params"]["longitude"] == 73.78
    assert w["location"] == {"latitude": 19.99, "longitude": 73.78}
    assert set(w) == {"location", "current", "forecast", "source"}


def test_no_provider_fields_leak(monkeypatch):
    monkeypatch.setattr(OC.httpx, "get", lambda *a, **k: _Resp(_hourly()))
    monkeypatch.setattr(OC, "_cache_path", lambda lat, lon: OC.Path("/nonexistent-cache.json"))
    raw = json.dumps(provider.get_canonical(1.0, 2.0))
    assert "temperature_2m" not in raw and "gfs_seamless" not in raw and "hourly" not in raw


def test_timeout_is_structured(monkeypatch):
    import httpx
    from data.openmeteo_client import DataUnavailable, ProviderTimeout
    def boom(*a, **k):
        raise httpx.ConnectTimeout("slow upstream")
    monkeypatch.setattr(OC.httpx, "get", boom)
    monkeypatch.setattr(OC, "_cache_path", lambda lat, lon: OC.Path("/nonexistent-cache.json"))
    try:
        provider.get_canonical(1.0, 2.0)
        raise AssertionError("no error")
    except ProviderTimeout as e:
        assert isinstance(e, DataUnavailable)


def test_http_and_malformed_are_structured(monkeypatch):
    import httpx
    from data.openmeteo_client import ProviderHTTPError, ProviderMalformed
    class _Bad:
        def raise_for_status(self):
            raise httpx.HTTPStatusError("500", request=None, response=None)
        def json(self):
            return {}
    monkeypatch.setattr(OC.httpx, "get", lambda *a, **k: _Bad())
    monkeypatch.setattr(OC, "_cache_path", lambda lat, lon: OC.Path("/nonexistent-cache.json"))
    try:
        provider.get_canonical(1.0, 2.0)
        raise AssertionError("no error")
    except ProviderHTTPError:
        pass
    monkeypatch.setattr(OC.httpx, "get", lambda *a, **k: _Resp({"hourly": {"time": []}}))
    try:
        provider.get_canonical(1.0, 2.0)
        raise AssertionError("no error")
    except ProviderMalformed:
        pass


def test_provider_mock_substitution(monkeypatch):
    wire_api(monkeypatch)
    class _Fake(OpenMeteoProvider):
        def get_forecast(self, lat, lon):
            return {"temp_c": 30.0, "humidity_pct": None, "wind_kph": None, "precip_mm": 0.0,
                    "precip_prob_pct": None, "weather_code": 1, "condition": "mainly_clear",
                    "observed_at": "t", "source": "fake", "lat": lat, "lon": lon}
    monkeypatch.setattr(M, "get_forecast", _Fake().get_forecast)
    d = c.post("/ask", json={"query": "Weather in Nashik?", "language": "en"}).json()
    assert d["forecast"]["temp_c"] == 30.0 and d["forecast"]["source"] == "fake"
