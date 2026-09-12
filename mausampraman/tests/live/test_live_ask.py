"""Live /ask smoke: Bhopal, Nashik, override. Needs internet."""
from fastapi.testclient import TestClient
from api.main import app

c = TestClient(app)


def test_live_nashik_shape():
    d = c.post("/ask", json={"query": "Nashik", "language": "en"}).json()
    assert d["location"]["name"] == "Nashik" and d["confidence"]["grade"] in ("A", "B", "C", "D")


def test_live_bhopal():
    d = c.post("/ask", json={"query": "What is the weather in Bhopal?", "location": "Bhopal", "language": "en"}).json()
    assert abs(d["location"]["lat"] - 23.26) < 0.6


def test_live_warning_override():
    d = c.post("/ask", json={"query": "nashik_coastal_test", "language": "en"}).json()
    assert d["confidence"]["warning_override"] is True


def test_live_daily_smoke():
    from data.openmeteo_client import get_daily
    periods = get_daily(19.99, 73.78)
    assert len(periods) == 3 and all(periods[0][k] is not None for k in ("date", "temp_max_c", "temp_min_c"))
