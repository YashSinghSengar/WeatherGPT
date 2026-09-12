from fastapi.testclient import TestClient
from api.main import app

c = TestClient(app)

CASES = [
    ("Will it rain tonight in Nashik?", 19.99, 73.79),
    ("Should I irrigate my grapes today in Nashik?", 19.99, 73.79),
    ("Weather in Pune", 18.52, 73.85),
    ("Rain tomorrow in Bhopal", 23.26, 77.41),
]


def test_location_resolution():
    for q, lat, lon in CASES:
        d = c.post("/ask", json={"query": q, "language": "en"}).json()
        assert abs(d["location"]["lat"] - lat) < 0.6, (q, d["location"])
        assert abs(d["location"]["lon"] - lon) < 0.6, (q, d["location"])


def test_explicit_location_field():
    d = c.post("/ask", json={"query": "Will it rain tonight?", "location": "Bhopal", "language": "en"}).json()
    assert abs(d["location"]["lat"] - 23.26) < 0.6


def test_unresolvable_location():
    r = c.post("/ask", json={"query": "xqztwkjvblorp zzzqq", "language": "en"})
    assert r.status_code == 404
