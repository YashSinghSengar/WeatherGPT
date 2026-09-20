"""Offline location tests. resolve_location itself stays live-tested in tests/live/."""
from fastapi.testclient import TestClient
from api.main import app

from tests.fixtures import CITIES, resolve_fake, wire_api

c = TestClient(app)


def test_location_resolution(monkeypatch):
    wire_api(monkeypatch)
    for q, city in (("Will it rain tonight in Nashik?", "Nashik"), ("Weather in Pune", "Pune"),
                    ("Rain tomorrow in Bhopal", "Bhopal"), ("What is the temperature in Delhi?", "Delhi"),
                    ("Is rain expected in Mumbai?", "Mumbai")):
        d = c.post("/ask", json={"query": q, "language": "en"}).json()
        assert d["location"]["name"] == city, (q, d["location"])
        assert d["location"]["lat"] == CITIES[city][0]


def test_explicit_location_field(monkeypatch):
    wire_api(monkeypatch)
    d = c.post("/ask", json={"query": "Will it rain tonight?", "location": "Bhopal", "language": "en"}).json()
    assert d["location"]["name"] == "Bhopal"


def test_unresolvable_location(monkeypatch):
    import api.main as M
    wire_api(monkeypatch)
    monkeypatch.setattr(M, "resolve_canonical", lambda q, loc=None: None)
    d = c.post("/ask", json={"query": "xqztwkjvblorp zzzqq", "language": "en"}).json()
    assert d["advisory"] is None and d["forecast"] is None and d["location"] is None


def test_resolve_fake_invalid():
    assert resolve_fake("Nashik")("xqztwkjvblorp zzzqq") is None
