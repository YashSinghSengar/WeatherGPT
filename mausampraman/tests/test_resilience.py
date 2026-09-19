import api.main as M
from data.openmeteo_client import DataUnavailable
from fastapi.testclient import TestClient
from phrasing.llm_phrase import phrase as llm_phrase

c = TestClient(M.app)

FORECAST = {"temp_c": 25.0, "humidity_pct": 50, "wind_kph": 10.0, "precip_mm": 3.0, "precip_prob_pct": 40,
            "weather_code": 61, "condition": "rain", "observed_at": "t", "source": "mock", "lat": 19.99, "lon": 73.78}
GREEN = {"district": "n", "severity": "green", "status": "district_not_covered", "headline": "h", "body": "", "issued_at": "d", "capture_date": "d"}
PER = {"gfs_seamless": {"temp_c": 25.0, "rain_mm": 2.0}, "ecmwf_ifs025": {"temp_c": 26.0, "rain_mm": 4.0}, "icon_seamless": {"temp_c": 25.5, "rain_mm": 3.0}}


def _base(monkeypatch):
    monkeypatch.setattr(M, "resolve_canonical", lambda q, loc=None: {"display_name": "Nashik", "latitude": 19.99, "longitude": 73.78, "country": "India", "state": "Maharashtra", "district": "Nashik", "source": "fixture"})
    monkeypatch.setattr(M, "get_forecast", lambda lat, lon: FORECAST)
    monkeypatch.setattr(M, "get_warning", lambda d: GREEN)
    monkeypatch.setattr(M, "prevruns_per_model", lambda lat, lon, day: PER)
    monkeypatch.setattr(M, "get_daily", lambda lat, lon: [])


def test_1_geocoder_failure_503(monkeypatch):
    def boom(q, loc=None):
        raise DataUnavailable("geo down")
    monkeypatch.setattr(M, "resolve_canonical", boom)
    r = c.post("/ask", json={"query": "Weather in Nashik?"})
    assert r.status_code == 503 and "location" in r.json()["detail"]


def test_2_forecast_failure_503_no_fabrication(monkeypatch):
    _base(monkeypatch)
    def boom(lat, lon):
        raise DataUnavailable("meteo down")
    monkeypatch.setattr(M, "get_forecast", boom)
    r = c.post("/ask", json={"query": "Weather in Nashik?"})
    assert r.status_code == 503 and "weather" in r.json()["detail"]


def test_3_divergence_failure_degrades(monkeypatch):
    _base(monkeypatch)
    def boom(lat, lon, day):
        raise DataUnavailable("prevruns down")
    monkeypatch.setattr(M, "prevruns_per_model", boom)
    d = c.post("/ask", json={"query": "Weather in Nashik?"}).json()
    assert d["confidence"]["grade"] == "D" and d["confidence"]["spread_mm"] is None
    assert "divergence-unavailable" in d["confidence"]["reasons"] and d["advisory"] is None


def test_4_warning_failure_unavailable(monkeypatch):
    _base(monkeypatch)
    def boom(d):
        raise OSError("disk gone")
    monkeypatch.setattr(M, "get_warning", boom)
    d = c.post("/ask", json={"query": "Weather in Nashik?"}).json()
    assert d["warning"]["status"] == "warning_data_unavailable"


def test_5_llm_failure_template(monkeypatch):
    import httpx
    monkeypatch.setenv("SARVAM_API_KEY", "x")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: 1 / 0)
    out = llm_phrase({"grade": "B", "action": "Act.", "rationale": "Why.", "values": {}}, "en")
    assert out.startswith("Grade B")
