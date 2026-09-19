"""Evidence + grounding verification (B8/B9). Deterministic, offline."""
import api.main as M
from confidence.evidence import build_evidence
from confidence.grounding import ground_check, verified_response
from fastapi.testclient import TestClient
from tests.fixtures import PER_NORMAL, wire_api

c = TestClient(M.app)
F = {"temp_c": 28.4, "humidity_pct": 70, "wind_kph": 11.2, "precip_mm": 0.4,
     "precip_prob_pct": 30, "weather_code": 2, "condition": "partly_cloudy",
     "observed_at": "t", "source": "openmeteo", "lat": 19.99, "lon": 73.78}
W = {"district": "n", "severity": "green", "status": "no_warning_confirmed", "headline": "h",
     "body": "", "issued_at": "d", "capture_date": "d", "source": "warnings-store"}
C = {"grade": "B", "warning_override": False, "spread_mm": 6.0, "skill_prior": 0.0,
     "drivers": {"spread_mm": 6.0}}
L = {"name": "Nashik", "lat": 19.99, "lon": 73.78, "state": "Maharashtra",
     "country": "India", "district": "Nashik", "source": "openmeteo-geocoding"}


def _ev(**kw):
    args = {"location": L, "forecast": F, "per_model": PER_NORMAL, "confidence": C, "warning": W,
            "advisory_status": "advisory_available",
            "advisory": {"rule_id": "r1", "citation": "c", "source": None},
            "crop": "grape", "stage": "veraison"}
    args.update(kw)
    return build_evidence(**args)


def test_evidence_location_preserved():
    assert _ev()["location"]["latitude"] == 19.99
    assert _ev()["location"]["display_name"] == "Nashik"


def test_evidence_weather_source():
    w = _ev()["weather"]
    assert w["source"] == "openmeteo" and w["forecast_time"] == "t"
    assert w["values"]["temperature"] == 28.4 and w["values"]["precipitation"] == 0.4


def test_evidence_model_provenance():
    assert _ev()["agreement"]["models_considered"] == ["ECMWF", "GFS", "ICON"]
    assert _ev()["weather"]["models"] == ["ECMWF", "GFS", "ICON"]


def test_evidence_agreement():
    a = _ev()["agreement"]
    assert a["grade"] == "B" and a["basis"]["spread_mm"] == 6.0


def test_evidence_warning_exact():
    w = _ev(warning={"status": "warning_data_unavailable", "severity": None, "source": "s"})["warning"]
    assert w["state"] == "warning_data_unavailable" and w["severity"] is None


def test_evidence_advisory_meta():
    a = _ev()["advisory"]
    assert (a["status"], a["rule_id"], a["citation"], a["crop"], a["stage"]) == \
        ("advisory_available", "r1", "c", "grape", "veraison")


def test_evidence_no_fabrication():
    e = build_evidence()
    assert e["weather"]["retrieved_at"] is None and e["agreement"]["grade"] is None
    assert e["warning"]["state"] is None and e["advisory"]["status"] is None


def test_ground_correct_temp():
    assert ground_check("Nashik 28.4C", F, W, C, None, L)["grounded"] is True


def test_ground_wrong_temp():
    r = ground_check("Nashik 35C heat", F, W, C, None, L)
    assert r["grounded"] is False and any(i.startswith("ungrounded-number") for i in r["issues"])


def test_ground_rounded_temp():
    assert ground_check("Nashik around 28C today", F, W, C, None, L)["grounded"] is True


def test_ground_wrong_precip_and_prob():
    r = ground_check("Nashik 9.9mm rain, 90% chance", F, W, C, None, L)
    assert r["grounded"] is False and len([i for i in r["issues"] if i.startswith("ungrounded-number")]) == 2


def test_ground_wrong_grade():
    r = ground_check("Nashik agreement A.", F, W, C, None, L)
    assert any(i.startswith("wrong-grade") for i in r["issues"])


def test_ground_wrong_location():
    assert "wrong-location" in ground_check("Delhi 28.4C.", F, W, C, None, L)["issues"]
    assert ground_check("Nashik district 28.4C.", F, W, C, None, L)["grounded"] is True


def test_ground_active_contradiction():
    wo = {**W, "status": "active_warning", "severity": "orange"}
    r = ground_check("No weather warning is active.", F, wo, C, None, L)
    assert r["grounded"] is False


def test_ground_unavailable_calm_fails():
    wu = {**W, "status": "warning_data_unavailable", "severity": None}
    assert "warning-false-calm" in ground_check("There is no warning.", F, wu, C, None, L)["issues"]
    wn = {**W, "status": "district_not_covered", "severity": None}
    assert "warning-false-calm" in ground_check("Your district has no warning.", F, wn, C, None, L)["issues"]


def test_ground_confirmed_calm_passes():
    assert ground_check("No warning is currently confirmed. Nashik 28.4C.", F, W, C, None, L)["grounded"] is True


def test_ground_blocked_advisory():
    kw = {"forecast": F, "warning": W, "confidence": C, "location": L,
          "advisory_status": "blocked_by_warning", "crop": "grape", "stage": "veraison"}
    assert "advisory-blocked" in ground_check("You should spray today.", **kw)["issues"]


def test_ground_invented_context():
    kw = {"forecast": F, "warning": W, "confidence": C, "location": L,
          "advisory_status": "needs_context", "crop": None, "stage": None}
    assert "advisory-invented-context" in ground_check("Since your grapes are flowering, spray.", **kw)["issues"]


def test_ground_unsupported_advisory():
    kw = {"forecast": F, "warning": W, "confidence": C, "location": L,
          "advisory_status": "no_matching_rule", "crop": "grape", "stage": "veraison"}
    assert "advisory-unsupported" in ground_check("Irrigate now.", **kw)["issues"]


def test_verified_valid_returned():
    kw = {"forecast": F, "warning": W, "confidence": C, "location": L}
    r = verified_response(lambda: "Nashik 28.4C.", "fallback", **kw)
    assert r["response"] == "Nashik 28.4C." and not r["fallback_used"] and r["grounded"]


def test_verified_invalid_falls_back():
    kw = {"forecast": F, "warning": W, "confidence": C, "location": L}
    r = verified_response(lambda: "Delhi 99.9C, no warning.", "Nashik 28.4C.", **kw)
    assert r["fallback_used"] and r["response"] == "Nashik 28.4C." and r["grounded"]
    assert any(i.startswith("ungrounded-number") for i in r["issues"])


def test_verified_generate_crash_falls_back():
    kw = {"forecast": F, "warning": W, "confidence": C, "location": L}
    def boom():
        raise RuntimeError("llm down")
    r = verified_response(boom, "Nashik 28.4C.", **kw)
    assert r["fallback_used"] and r["grounded"]


def test_ask_evidence_matches_and_single_fetch(monkeypatch):
    wire_api(monkeypatch)
    calls = {"n": 0}
    real = M.get_forecast
    def counting(lat, lon):
        calls["n"] += 1
        return real(lat, lon)
    monkeypatch.setattr(M, "get_forecast", counting)
    d = c.post("/ask", json={"query": "Will it rain tonight in Nashik?", "language": "en"}).json()
    assert calls["n"] == 1 and d["evidence"]["weather"]["values"]["precipitation"] == d["forecast"]["precip_mm"]
    assert d["evidence"]["location"]["latitude"] == d["location"]["lat"]
    assert d["evidence"]["agreement"]["grade"] == d["confidence"]["grade"]
    assert d["evidence"]["warning"]["state"] == d["warning"]["status"]


def test_ask_evidence_no_warning_state_drift(monkeypatch):
    wire_api(monkeypatch, warning="orange")
    d = c.post("/ask", json={"query": "Is there a warning for Pune?", "language": "en"}).json()
    assert d["evidence"]["warning"]["state"] == "active_warning" == d["warning"]["status"]
