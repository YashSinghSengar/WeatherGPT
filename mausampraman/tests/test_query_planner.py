"""Query planner (B4/B5). Deterministic flags + gated execution. Offline."""
import api.main as M
from api.planner import plan_query
from fastapi.testclient import TestClient
from tests.fixtures import wire_api

c = TestClient(M.app)


def test_plan_flags_per_intent():
    assert plan_query("weather_current") == {"intent": "weather_current", "location_required": True,
        "current_weather": True, "forecast": True, "agreement": True, "warnings": True, "daily": True, "advisory": False}
    rain = plan_query("forecast_rain")
    assert rain["forecast"] and rain["agreement"] and not rain["advisory"]
    warn = plan_query("warning_status")
    assert warn["warnings"] and not warn["forecast"] and not warn["advisory"]
    agri = plan_query("agriculture_advice")
    assert all(agri[k] for k in ("forecast", "agreement", "warnings", "advisory"))
    conf = plan_query("confidence_explanation")
    assert conf["agreement"] and not conf["forecast"] and not conf["advisory"]
    unsup = plan_query("unsupported")
    assert not any(unsup[k] for k in ("current_weather", "forecast", "agreement", "warnings", "daily", "advisory"))
    assert plan_query("nope")["intent"] == "nope" and not plan_query("nope")["warnings"]


def _counts(monkeypatch):
    wire_api(monkeypatch)
    calls = {"forecast": 0, "prevruns": 0, "warning": 0, "daily": 0}
    import tests.fixtures as F
    orig_forecast = M.get_forecast
    def counting_forecast(lat, lon):
        calls["forecast"] += 1
        return orig_forecast(lat, lon)
    def counting_prevruns(lat, lon, day):
        calls["prevruns"] += 1
        return F.PER_NORMAL
    def counting_warning(d):
        calls["warning"] += 1
        return F.warning_green(d)
    def counting_daily(lat, lon):
        calls["daily"] += 1
        return []
    monkeypatch.setattr(M, "get_forecast", counting_forecast)
    monkeypatch.setattr(M, "prevruns_per_model", counting_prevruns)
    monkeypatch.setattr(M, "get_warning", counting_warning)
    monkeypatch.setattr(M, "get_daily", counting_daily)
    return calls


def test_current_skips_advisory_single_fetch(monkeypatch):
    calls = _counts(monkeypatch)
    d = c.post("/ask", json={"query": "What is the temperature in Delhi?", "language": "en"}).json()
    assert calls["forecast"] == 1 and calls["prevruns"] == 1 and d["advisory"] is None
    assert d["forecast"]["temp_c"] == 25.0 and d["confidence"]["grade"] == "A"


def test_rain_uses_shared_model_data(monkeypatch):
    calls = _counts(monkeypatch)
    d = c.post("/ask", json={"query": "Will it rain tonight in Nashik?", "language": "en"}).json()
    assert calls["forecast"] == 1 and calls["prevruns"] == 1  # no duplicate fetch for agreement
    assert "3.0mm" in d["answer"] and d["confidence"]["spread_mm"] == 2.0


def test_warning_skips_weather_and_advisory(monkeypatch):
    calls = _counts(monkeypatch)
    d = c.post("/ask", json={"query": "Is there a warning for Pune?", "language": "en"}).json()
    assert calls["forecast"] == 0 and calls["daily"] == 0 and d["advisory"] is None
    assert calls["warning"] == 1 and d["forecast"] is None
    assert d["confidence"]["grade"] in ("A", "B", "C", "D")


def test_agri_gets_everything(monkeypatch):
    calls = _counts(monkeypatch)
    d = c.post("/ask", json={"query": "Should I irrigate grapes in Nashik?",
                             "crop": "grape", "stage": "veraison", "language": "en"}).json()
    assert calls["forecast"] == 1 and calls["prevruns"] == 1 and calls["warning"] == 1
    assert d["advisory"] is not None and d["advisory"]["rule_id"]


def test_unsupported_skips_provider(monkeypatch):
    calls = _counts(monkeypatch)
    monkeypatch.setattr(M, "resolve_canonical", lambda q, loc=None: None)
    def boom(lat, lon):
        raise AssertionError("weather called")
    monkeypatch.setattr(M, "get_forecast", boom)
    d = c.post("/ask", json={"query": "Who won the cricket match yesterday?", "language": "en"}).json()
    assert d["forecast"] is None and calls["prevruns"] == 0 and calls["warning"] == 0


def test_provider_failure_propagates(monkeypatch):
    from data.openmeteo_client import DataUnavailable
    wire_api(monkeypatch)
    monkeypatch.setattr(M, "get_forecast", lambda lat, lon: (_ for _ in ()).throw(DataUnavailable("meteo down")))
    r = c.post("/ask", json={"query": "Weather in Nashik?"})
    assert r.status_code == 503
