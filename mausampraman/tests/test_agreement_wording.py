import api.main as M
from confidence.grounding import ground_check
from phrasing.templates import phrase as template_phrase

LOC = {"name": "Nashik", "lat": 19.99, "lon": 73.78, "state": "u", "country": "u"}
F = {"temp_c": 25.0, "humidity_pct": 0, "wind_kph": 0.0, "precip_mm": 3.0, "condition": "rain", "source": "m", "lat": 19.99, "lon": 73.78}
W = {"district": "n", "severity": "green", "headline": "No warning", "body": "", "issued_at": "d", "capture_date": "d"}
ADV = {"advice_en": "Do X.", "advice_hi": "X."}


def _conf(g):
    return {"grade": g, "warning_override": False, "spread_mm": 1.0, "skill_prior": 0.0, "drivers": {"spread_mm": 1.0}}


def test_composed_answers_use_agreement():
    for intent in ("weather_current", "forecast_rain", "warning_status", "confidence_explanation"):
        out = M._compose(intent, LOC, F, W, _conf("B"))
        assert "greement" in out and "onfidence" not in out and "%" not in out


def test_template_phrase_uses_agreement():
    for g in ("A", "B", "C", "D"):
        out = template_phrase(ADV, F, W, _conf(g), LOC, "en")
        assert f"Agreement: {g}" in out and "Confidence" not in out


def test_grounding_accepts_agreement_grades():
    for g in ("A", "B", "C", "D"):
        r = ground_check(f"Nashik: 25.0C. Agreement: {g}.", F, W, _conf(g))
        assert r["grounded"] is True, (g, r)
    r = ground_check("Nashik: 25.0C. Agreement: D.", F, W, _conf("A"))
    assert any(i.startswith("wrong-grade") for i in r["issues"])
