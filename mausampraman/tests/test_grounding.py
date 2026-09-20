from confidence.grounding import ground_check

F = {"temp_c": 25.0, "humidity_pct": 0, "wind_kph": 0.0, "precip_mm": 3.0, "condition": "rain", "source": "m", "lat": 19.99, "lon": 73.78}
W = {"district": "nashik", "severity": "green", "headline": "No warning", "body": "", "issued_at": "d", "capture_date": "d"}
WO = {**W, "severity": "orange", "headline": "Heavy rainfall likely", "body": "Stay indoors."}
C = {"grade": "A", "warning_override": False, "spread_mm": 0.6, "skill_prior": 0.0, "drivers": {"spread_mm": 0.6}}
A = {"crop": "grape", "stage": "veraison", "rule_id": "veraison_low_spread", "advice_en": "Models agree proceed.", "advice_hi": "x", "citation": "c", "strength": "strong", "safe": True}
L = {"name": "Nashik", "lat": 19.99, "lon": 73.78, "state": "u", "country": "u"}
GOOD = "Nashik: 25.0C, rain. Warning: green. Confidence: A. Advice: Models agree proceed."


def test_valid_grounded():
    assert ground_check(GOOD, F, W, C, A, L) == {"grounded": True, "issues": [],
                                                "checked": ["numbers", "location", "agreement", "warning"]}


def test_correct_value():
    assert ground_check("Nashik 3.0mm rain", F, W)["grounded"] is True


def test_wrong_value():
    r = ground_check("Nashik 99.9C heat", F, W)
    assert r["grounded"] is False and any(i.startswith("ungrounded-number") for i in r["issues"])


def test_warning_omitted():
    r = ground_check("Nashik: 25.0C, all calm.", F, WO, C)
    assert "warning-omitted" in r["issues"]


def test_warning_contradicted():
    r = ground_check("Nashik: 25.0C, orange no warning at all.", F, WO, C)
    assert "warning-contradicted" in r["issues"]


def test_wrong_grade():
    r = ground_check("Nashik: 25.0C. Confidence: D.", F, W, C)
    assert any(i.startswith("wrong-grade") for i in r["issues"])


def test_wrong_location():
    r = ground_check("Pune: 25.0C.", F, W, None, None, L)
    assert "wrong-location" in r["issues"]


def test_missing_rule():
    r = ground_check(GOOD, F, W, C, {**A, "rule_id": ""}, L)
    assert "missing-rule-id" in r["issues"]


def test_strength_mismatch_and_citation():
    r = ground_check(GOOD, F, W, {**C, "grade": "D"}, {**A, "citation": ""}, L)
    assert "strength-mismatch" in r["issues"] and "missing-citation" in r["issues"]


def test_unsupported_number_and_empty():
    assert any(i.startswith("ungrounded-number") for i in ground_check("Nashik wind 45.", F, W)["issues"])
    assert ground_check("", F, W) == {"grounded": False, "issues": ["empty-draft"],
                                        "checked": ["numbers", "location", "agreement", "warning"]}
