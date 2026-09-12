"""Offline scaffold tests. All externals mocked via tests.fixtures."""
from fastapi.testclient import TestClient
from api.main import app

from tests.fixtures import CITIES, PER_NORMAL, forecast, warning_orange, wire_api

c = TestClient(app)


def test_health():
    assert c.get("/health").json() == {"status": "ok"}


def test_ask_shape_en(monkeypatch):
    wire_api(monkeypatch, city="Nashik")
    r = c.post("/ask", json={"query": "Nashik", "lang": "en", "crop": "grape"})
    d = r.json()
    for k in ("answer", "confidence", "provenance", "advisory", "location", "warning", "forecast"):
        assert k in d, k
    assert d["confidence"]["grade"] in ("A", "B", "C", "D")
    assert d["location"]["lat"] == CITIES["Nashik"][0]


def test_ask_hi(monkeypatch):
    wire_api(monkeypatch, city="Pune")
    r = c.post("/ask", json={"query": "Pune", "lang": "hi", "crop": "grape"})
    assert "Advice" in r.json()["answer"] or r.json()["answer"]


def test_stubs(monkeypatch):
    import api.main as M
    from data.openmeteo_client import divergence_scenario_from_models
    from confidence.engine import grade
    from confidence.grounding import ground_check
    from advisory.engine import get_advisory
    from phrasing.templates import phrase

    monkeypatch.setattr(M, "get_warning", lambda d: warning_orange())
    lat, lon = CITIES["Nashik"]
    f = forecast("Nashik")
    w = warning_orange()
    assert w["severity"] == "orange" and "capture_date" in w
    dv = divergence_scenario_from_models(lat, lon, PER_NORMAL)
    assert set(dv) == set(f)
    conf = grade(PER_NORMAL, w, 0.0, 2)
    adv = get_advisory("grape", "veraison", {**conf, "drivers": {"spread_mm": 2.0}})
    assert adv and adv["strength"] in ("strong", "moderate", "watch_only")
    assert get_advisory("grape", "veraison", {"drivers": {}}) is None
    assert get_advisory("wheat", "veraison", conf) is None
    txt = phrase(adv, f, w, conf, {"name": "Nashik"}, "en")
    assert ground_check(txt, f, w)["grounded"]


def test_warning_override(monkeypatch):
    wire_api(monkeypatch, city="Nashik", warning="orange")
    r = c.post("/ask", json={"query": "nashik_coastal_test", "lang": "en", "crop": "grape"})
    d = r.json()
    assert d["confidence"]["grade"] == "D"
    assert d["confidence"]["warning_override"] is True
    assert d["warning"]["severity"] == "orange"
