import api.main as M
from fastapi.testclient import TestClient

c = TestClient(M.app)


def test_allowed_origins_dev_default(monkeypatch):
    monkeypatch.delenv("FRONTEND_ORIGIN", raising=False)
    assert "http://localhost:3000" in M.allowed_origins()
    assert "http://localhost:3001" in M.allowed_origins()


def test_allowed_origins_prod_env(monkeypatch):
    monkeypatch.setenv("FRONTEND_ORIGIN", "https://mausampraman.vercel.app")
    assert M.allowed_origins() == ["https://mausampraman.vercel.app"]


def test_local_origin_preflight():
    r = c.options("/ask", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_disallowed_origin_rejected():
    r = c.options("/ask", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in r.headers


def test_local_frontend_to_backend(monkeypatch):
    from tests.fixtures import wire_api
    wire_api(monkeypatch)
    r = c.post("/ask", json={"query": "Weather in Nashik?"}, headers={"Origin": "http://localhost:3000"})
    assert r.status_code == 200 and r.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_health_open():
    assert c.get("/health").json() == {"status": "ok"}
