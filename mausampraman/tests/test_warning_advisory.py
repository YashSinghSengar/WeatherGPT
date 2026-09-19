"""Warning + advisory architecture (B6/B7). Deterministic, offline."""
import api.main as M
from advisory.engine import decide_advisory, get_advisory
from data.warnings import canonical_warning, is_active, warning_key_for_location
from fastapi.testclient import TestClient
from tests.fixtures import PER_NORMAL, warning_green, warning_orange, wire_api

c = TestClient(M.app)
CONF = {"grade": "B", "warning_override": False, "spread_mm": 6.0,
        "skill_prior": 0.0, "drivers": {"spread_mm": 6.0}}
ADV = {"crop": "grape", "stage": "veraison", "rule_id": "r", "advice_en": "Do X.",
       "advice_hi": "X.", "citation": "c", "strength": "strong", "safe": True}


def test_active_warning_canonical():
    w = canonical_warning({"district": "n", "severity": "orange", "status": "active_warning",
                           "headline": "H", "body": "B", "issued_at": "d", "capture_date": "d"})
    assert w["state"] == "active_warning" and w["severity"] == "orange"
    assert w["source"] == "warnings-store" and is_active(w)


def test_severity_scale_preserved():
    for sev, active in (("green", False), ("yellow", True), ("orange", True), ("red", True)):
        w = canonical_warning({"district": "n", "severity": sev,
                               "status": "active_warning" if active else "no_warning_confirmed",
                               "headline": "h", "body": "", "issued_at": "d", "capture_date": "d"})
        assert (w["severity"] == sev) and (is_active(w) == active)


def test_unavailable_never_green():
    w = canonical_warning({"district": "n", "severity": "green", "headline": "h", "body": "",
                           "issued_at": "", "capture_date": "", "status": "warning_data_unavailable"})
    assert w["state"] == "warning_data_unavailable" and w["severity"] is None and not is_active(w)


def test_not_covered_distinct_from_confirmed():
    covered = canonical_warning(warning_green() | {"status": "no_warning_confirmed", "severity": "green"})
    missing = canonical_warning(warning_green())
    assert covered["state"] == "no_warning_confirmed" and covered["severity"] == "green"
    assert missing["state"] == "district_not_covered" and missing["severity"] is None


def test_key_from_canonical_location():
    assert warning_key_for_location({"display_name": "Nashik", "district": "Ahilyanagar"}) == "ahilyanagar"
    assert warning_key_for_location({"display_name": "New Delhi"}) == "new"
    assert warning_key_for_location(None) == ""


def test_override_preserved():
    from confidence.engine import grade
    assert grade(PER_NORMAL, warning_orange(), 0.0, 2)["warning_override"] is True
    assert grade(PER_NORMAL, warning_green(), 0.0, 2)["warning_override"] is False


def test_store_failure_no_fabrication(monkeypatch):
    import data.warning_store as WS
    monkeypatch.setattr(WS, "DIR", WS.DIR / "definitely-missing-dir")
    w = canonical_warning(WS.get_warning("Nashik"))
    assert w["state"] in ("warning_data_unavailable", "district_not_covered") and not is_active(w)


def test_agri_opt_in_and_decide():
    assert decide_advisory("grape", "veraison", CONF, "no_warning_confirmed", ADV)["status"] == "advisory_available"
    assert decide_advisory(None, "veraison", CONF, "no_warning_confirmed", None)["status"] == "needs_context"
    assert decide_advisory("grape", None, CONF, "no_warning_confirmed", None)["missing"] == ["stage"]
    assert decide_advisory("grape", "veraison", CONF, "no_warning_confirmed", None)["status"] == "no_matching_rule"
    assert decide_advisory("grape", "veraison", None, "no_warning_confirmed", None)["status"] == "insufficient_weather_data"


def test_warning_constrains_advisory():
    assert decide_advisory("grape", "veraison", CONF, "active_warning", ADV)["status"] == "blocked_by_warning"
    assert decide_advisory("grape", "veraison", CONF, "warning_data_unavailable", ADV)["status"] == "warning_data_unavailable"
    d = decide_advisory("grape", "veraison", CONF, "district_not_covered", ADV)
    assert d["status"] == "advisory_available"  # uncovered is not a calm claim; rules still decide


def test_rules_untouched():
    adv = get_advisory("grape", "veraison", {**CONF, "drivers": {"spread_mm": 2.0}})
    assert adv and adv["rule_id"] and adv["strength"] in ("strong", "moderate", "watch_only")
    assert get_advisory("grape", "veraison", {"drivers": {}}) is None


def test_blocked_end_to_end(monkeypatch):
    wire_api(monkeypatch, warning="orange")
    d = c.post("/ask", json={"query": "Should I irrigate grapes in Nashik?",
                             "crop": "grape", "stage": "veraison", "language": "en"}).json()
    assert d["advisory"] is None and "warning" in d["answer"] and "safe" not in d["answer"].lower()


def test_weather_skips_advisory_warning_kept(monkeypatch):
    wire_api(monkeypatch)
    d = c.post("/ask", json={"query": "What is the weather in Bhopal?", "language": "en"}).json()
    assert d["advisory"] is None and d["warning"]["state"] == "district_not_covered"


def test_unsupported_skips_warning_advisory(monkeypatch):
    wire_api(monkeypatch)
    monkeypatch.setattr(M, "resolve_canonical", lambda q, loc=None: None)
    monkeypatch.setattr(M, "get_warning", lambda d: (_ for _ in ()).throw(AssertionError("warning called")))
    d = c.post("/ask", json={"query": "Who won the cricket match yesterday?", "language": "en"}).json()
    assert d["warning"] is None and d["advisory"] is None
