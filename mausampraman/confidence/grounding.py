"""Deterministic grounding validator. Draft vs evidence, no LLM."""
import re

STRENGTH = {"A": "strong", "B": "strong", "C": "moderate", "D": "watch_only"}
CONTRA = ("no warning", "no warnings", "no alert", "all clear", "perfectly safe")


def _nums(text: str) -> list:
    return [float(m) for m in re.findall(r"[+-]?\d+(?:\.\d+)?", str(text or ""))]


def _words(s: object) -> list:
    return [w.lower() for w in re.findall(r"[A-Za-z]+", str(s or "")) if len(w) > 3]


def ground_check(draft: str, forecast: dict, warning: dict, confidence: dict | None = None, advisory: dict | None = None, location: dict | None = None) -> dict:
    issues: list[str] = []
    if not draft or not str(draft).strip():
        return {"grounded": False, "issues": ["empty-draft"]}
    text, low = str(draft), str(draft).lower()
    forecast, warning = forecast or {}, warning or {}

    allowed = [float(v) for v in forecast.values() if isinstance(v, (int, float))]
    if confidence:
        for k in ("spread_mm", "skill_prior"):
            if isinstance(confidence.get(k), (int, float)):
                allowed.append(float(confidence[k]))
        for v in (confidence.get("drivers") or {}).values():
            if isinstance(v, (int, float)):
                allowed.append(float(v))
    for n in _nums(text):
        if not any(n == a for a in allowed):
            issues.append(f"ungrounded-number:{n}")

    sev = str(warning.get("severity", "green")).lower()
    if sev != "green":
        head = _words(warning.get("headline")) + _words(warning.get("body"))
        if sev not in low and not (head and all(w in low for w in head)):
            issues.append("warning-omitted")
        if any(c in low for c in CONTRA):
            issues.append("warning-contradicted")

    if confidence and confidence.get("grade"):
        m = re.search(r"confidence\s*[:\-]?\s*([A-Da-d])", low)
        if m and m.group(1).upper() != confidence["grade"]:
            issues.append(f"wrong-grade:{m.group(1).upper()}")

    if advisory is not None:
        if not advisory.get("rule_id"):
            issues.append("missing-rule-id")
        adv_en, adv_hi = _words(advisory.get("advice_en")), _words(advisory.get("advice_hi"))
        covered = (adv_en and all(w in low for w in adv_en)) or (adv_hi and all(w in low for w in adv_hi))
        if (adv_en or adv_hi) and not covered and not re.search(r"[\u0900-\u097F]", text):
            issues.append("advice-mismatch")
        if not advisory.get("citation"):
            issues.append("missing-citation")
        if confidence and confidence.get("grade") and advisory.get("strength") != STRENGTH.get(confidence["grade"]):
            issues.append("strength-mismatch")

    if location and location.get("name"):
        if str(location["name"]).lower() not in low:
            issues.append("wrong-location")

    if forecast.get("humidity_pct", 0) == 0 and re.search(r"humidity\D{0,5}0\s?%", low):
        issues.append("unconfirmed-data:humidity")
    if forecast.get("wind_kph", 0.0) == 0.0 and re.search(r"wind\D{0,5}0(\.0)?\s?(km/h|kph)", low):
        issues.append("unconfirmed-data:wind")

    return {"grounded": not issues, "issues": issues}
