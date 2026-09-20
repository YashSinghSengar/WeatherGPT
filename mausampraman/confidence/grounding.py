"""Deterministic grounding validator. Draft vs evidence, no LLM."""
import re

STRENGTH = {"A": "strong", "B": "strong", "C": "moderate", "D": "watch_only"}
CONTRA = ("no warning", "no warnings", "no alert", "all clear", "perfectly safe")
CALM = CONTRA + ("no active warning", "no warnings active", "without warning", "without any warning")
UNKNOWN_WARNING = ("warning_data_unavailable", "district_not_covered")
TEMP_KEYS = ("temp_c", "temperature", "feels_like")
TEMP_TOLERANCE = 0.5  # ponytail: whole-degree rounding only; all other numbers exact
ACTION_VERBS = ("spray", "irrigate", "irrigation", "harvest", "sow", "sowing",
                "fertilize", "fertilizer", "fertiliser", "pesticide", "fungicide", "prune")
CROP_WORDS = ("grape", "angoor", "wheat", "rice", "crop", "fasal")
STAGE_WORDS = ("flowering", "fruit-set", "fruitset", "veraison", "harvest")


def _nums(text: str) -> list:
    return [float(m) for m in re.findall(r"[+-]?\d+(?:\.\d+)?", str(text or ""))]


def _words(s: object) -> list:
    return [w.lower() for w in re.findall(r"[A-Za-z]+", str(s or "")) if len(w) > 3]


def ground_check(draft: str, forecast: dict, warning: dict, confidence: dict | None = None, advisory: dict | None = None, location: dict | None = None,
                 advisory_status: str | None = None, crop: str | None = None, stage: str | None = None) -> dict:
    issues: list[str] = []
    checked = ["numbers", "location", "agreement", "warning"]
    if not draft or not str(draft).strip():
        return {"grounded": False, "issues": ["empty-draft"], "checked": checked}
    text, low = str(draft), str(draft).lower()
    forecast, warning = forecast or {}, warning or {}

    allowed, allowed_temp = [], []
    for k, v in forecast.items():
        if isinstance(v, (int, float)):
            (allowed_temp if k in TEMP_KEYS else allowed).append(float(v))
    if confidence:
        for k in ("spread_mm", "skill_prior"):
            if isinstance(confidence.get(k), (int, float)):
                allowed.append(float(confidence[k]))
        for v in (confidence.get("drivers") or {}).values():
            if isinstance(v, (int, float)):
                allowed.append(float(v))
    for n in _nums(text):
        if not any(n == a for a in allowed + allowed_temp) and not any(abs(n - a) <= TEMP_TOLERANCE for a in allowed_temp):
            issues.append(f"ungrounded-number:{n}")

    sev = str(warning.get("severity", "green")).lower()
    wstatus = warning.get("status") or warning.get("state")
    if wstatus in UNKNOWN_WARNING:
        if any(c in low for c in CALM):
            issues.append("warning-false-calm")
    elif sev != "green":
        head = _words(warning.get("headline")) + _words(warning.get("body"))
        if sev not in low and not (head and all(w in low for w in head)):
            issues.append("warning-omitted")
        if any(c in low for c in CONTRA):
            issues.append("warning-contradicted")

    if confidence and confidence.get("grade"):
        m = re.search(r"(?:confidence|agreement)\s*[:\-]?\s*([A-Da-d])", low)
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

    if location:
        names = [str(location.get(k) or "").lower() for k in ("name", "display_name", "district", "state")]
        names = [n for n in names if len(n) > 2]
        if names and not any(n in low for n in names):
            issues.append("wrong-location")

    if forecast.get("humidity_pct") is None and re.search(r"humidity", low):
        issues.append("unconfirmed-data:humidity")
    if forecast.get("wind_kph") is None and re.search(r"wind", low):
        issues.append("unconfirmed-data:wind")

    if advisory_status is not None:
        checked.append("advisory")
        if advisory_status == "blocked_by_warning":
            if any(v in low for v in ACTION_VERBS) or "safe" in low:
                issues.append("advisory-blocked")
        elif advisory_status == "needs_context":
            if (not crop and any(w in low for w in CROP_WORDS)) or (not stage and any(w in low for w in STAGE_WORDS)):
                issues.append("advisory-invented-context")
        elif advisory_status in ("no_matching_rule", "insufficient_weather_data", "warning_data_unavailable"):
            if any(v in low for v in ACTION_VERBS):
                issues.append("advisory-unsupported")

    return {"grounded": not issues, "issues": issues, "checked": checked}


def verified_response(generate, fallback: str, **ground_kwargs) -> dict:
    """LLM output treated as untrusted: valid returns it, else deterministic fallback."""
    try:
        draft = generate()
    except Exception:
        draft = ""
    check = ground_check(draft or "", **ground_kwargs)
    if (draft or "").strip() and check["grounded"]:
        return {"response": draft, "grounded": True, "issues": [],
                "checked": check["checked"], "fallback_used": False}
    back = ground_check(fallback, **ground_kwargs)
    return {"response": fallback, "grounded": back["grounded"], "issues": check["issues"],
            "checked": check["checked"], "fallback_used": True}
