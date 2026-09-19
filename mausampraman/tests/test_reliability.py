"""Reliability (B10). Timeouts, malformed, cache safety, input safety. Offline."""
import json
import logging

import api.main as M
import data.openmeteo_client as OC
from confidence.engine import feed_age_minutes
from fastapi.testclient import TestClient
from tests.fixtures import wire_api

c = TestClient(M.app)


def test_weather_timeout_structured_503(monkeypatch):
    import httpx
    wire_api(monkeypatch)
    monkeypatch.setattr(M, "resolve_canonical",
                        lambda q, loc=None: {"display_name": "Nashik", "latitude": 19.99,
                                             "longitude": 73.78, "source": "fixture"})
    def slow(*a, **k):
        raise httpx.ConnectTimeout("slow upstream")
    monkeypatch.setattr(OC.httpx, "get", slow)
    monkeypatch.setattr(OC, "_cache_path", lambda lat, lon: OC.Path("/nonexistent-cache.json"))
    monkeypatch.setattr(M, "get_forecast", OC.get_forecast)
    r = c.post("/ask", json={"query": "Weather in Nashik?", "language": "en"})
    assert r.status_code == 503 and "weather" in r.json()["detail"]
    assert "Traceback" not in r.text


def test_geocoder_timeout_503(monkeypatch):
    import httpx
    import data.geocoder as G
    wire_api(monkeypatch)
    def slow(*a, **k):
        raise httpx.ConnectTimeout("geo slow")
    monkeypatch.setattr(G.httpx, "get", slow)
    monkeypatch.setattr(M, "resolve_canonical", G.resolve_canonical)
    r = c.post("/ask", json={"query": "Weather in Nashik?", "language": "en"})
    assert r.status_code == 503 and "location" in r.json()["detail"]


def test_malformed_provider_no_fabrication(monkeypatch):
    wire_api(monkeypatch)
    monkeypatch.setattr(M, "resolve_canonical",
                        lambda q, loc=None: {"display_name": "Nashik", "latitude": 19.99,
                                             "longitude": 73.78, "source": "fixture"})
    class _Bad:
        def raise_for_status(self):
            pass
        def json(self):
            return {"hourly": None}
    monkeypatch.setattr(OC.httpx, "get", lambda *a, **k: _Bad())
    monkeypatch.setattr(OC, "_cache_path", lambda lat, lon: OC.Path("/nonexistent-cache.json"))
    monkeypatch.setattr(M, "get_forecast", OC.get_forecast)
    r = c.post("/ask", json={"query": "Weather in Nashik?", "language": "en"})
    assert r.status_code == 503


def test_sarvam_timeout_falls_back(monkeypatch):
    import httpx
    from phrasing.llm_phrase import phrase as llm_phrase
    monkeypatch.setenv("SARVAM_API_KEY", "x")
    def slow(*a, **k):
        raise httpx.ReadTimeout("sarvam slow")
    monkeypatch.setattr(httpx, "post", slow)
    out = llm_phrase({"grade": "B", "action": "Act.", "rationale": "Why.", "values": {}}, "en")
    assert out.startswith("Grade B")


def test_failure_never_cached(tmp_path, monkeypatch):
    monkeypatch.setattr(OC, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(OC, "_cache_path", lambda lat, lon: tmp_path / "f.json")
    def boom(*a, **k):
        raise OC.DataUnavailable("down")
    monkeypatch.setattr(OC.httpx, "get", boom)
    try:
        OC.get_canonical_weather(1.0, 2.0)
        raise AssertionError("no error")
    except OC.DataUnavailable:
        pass
    assert list(tmp_path.iterdir()) == []


def test_corrupt_cache_misses_safely(tmp_path, monkeypatch):
    monkeypatch.setattr(OC, "_cache_path", lambda lat, lon: tmp_path / "f.json")
    (tmp_path / "f.json").write_text("{not json")
    assert OC._cache_hit(tmp_path / "f.json") is None
    assert feed_age_minutes(1.0, 2.0) == 0.0


def test_input_safety(monkeypatch):
    wire_api(monkeypatch)
    for body in ({"query": "", "language": "en"},
                 {"query": "x" * 10000, "language": "en"},
                 {"query": "Weather?", "language": "xx"},
                 {"query": "Weather in Nashik?", "crop": 5},
                 {"query": "Weather?", "location": 7},
                 {"query": "hi"}):
        r = c.post("/ask", json=body)
        assert r.status_code in (200, 404, 422, 503), (body, r.status_code)
        assert "Traceback" not in r.text


def test_stages_observed(monkeypatch, caplog):
    import json as J
    wire_api(monkeypatch)
    with caplog.at_level(logging.INFO, logger="mausampraman"):
        c.post("/ask", json={"query": "Weather in Nashik?", "language": "en"})
    recs = [r for r in caplog.records if r.name == "mausampraman"]
    last = J.loads(recs[-1].getMessage())
    assert set(last["stages"]) >= {"intent_plan", "resolve", "weather", "warning", "agreement", "grounding"}
    assert last["duration_ms"] >= 0 and last["request_id"]


def test_no_secret_in_logs(monkeypatch, caplog):
    monkeypatch.setenv("SARVAM_API_KEY", "sekret-key-123")
    wire_api(monkeypatch)
    with caplog.at_level(logging.INFO, logger="mausampraman"):
        c.post("/ask", json={"query": "Weather in Nashik?", "language": "en"})
    blob = " ".join(r.getMessage() for r in caplog.records if r.name == "mausampraman")
    assert "sekret-key-123" not in blob and "Bearer" not in blob
