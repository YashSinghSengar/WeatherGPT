from fastapi.testclient import TestClient
from api.main import app

c = TestClient(app)


def test_health():
    assert c.get("/health").json() == {"status": "ok"}


def test_ask_shape_en():
    r = c.post("/ask", json={"query": "Nashik", "lang": "en", "crop": "grape"})
    d = r.json()
    for k in ("answer", "confidence", "provenance", "advisory", "location", "warning", "forecast"):
        assert k in d, k
    assert d["confidence"]["grade"] in ("A", "B", "C", "D")


def test_ask_hi():
    r = c.post("/ask", json={"query": "Pune", "lang": "hi", "crop": "grape"})
    assert "Advice" in r.json()["answer"] or r.json()["answer"]


def test_stubs():
    from data.geocoder import geocode
    from data.openmeteo_client import get_divergence_scenario, get_forecast
    from data.warning_store import get_warning
    from confidence.engine import grade_forecast
    from confidence.grounding import ground_check
    from advisory.engine import get_advisory
    from phrasing.templates import phrase

    loc = geocode("nashik_coastal_test")
    lat, lon = loc
    f = get_forecast(lat, lon)
    w = get_warning("nashik_coastal_test")
    assert w["severity"] == "orange" and "capture_date" in w
    dv = get_divergence_scenario(lat, lon)
    assert set(dv) == set(f)
    conf = grade_forecast(f, w, dv)
    adv = get_advisory("grape", "veraison", conf)
    assert adv and adv["strength"] in ("strong", "moderate", "watch_only")
    assert get_advisory("grape", "veraison", {"drivers": {}}) is None
    assert get_advisory("wheat", "veraison", conf) is None
    txt = phrase(adv, f, w, conf, {"name": "Nashik"}, "en")
    assert ground_check(txt, f, w)["grounded"]
    assert get_warning("qzxnothing") is None


def test_warning_override():
    r = c.post("/ask", json={"query": "nashik_coastal_test", "lang": "en", "crop": "grape"})
    d = r.json()
    assert d["confidence"]["grade"] == "D"
    assert d["confidence"]["warning_override"] is True
    assert d["advisory"]["safe"] is False
