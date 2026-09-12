"""Deterministic templates. Only wording layer."""
from data.warning_store import STATUS_TEXT


def _warn_state(warning: dict) -> str:
    sev = warning.get("severity", "green")
    return sev if warning.get("status") == "active_warning" else STATUS_TEXT.get(warning.get("status", ""), sev)


def render_template(payload: dict, language: str) -> str:
    p = payload or {}
    grade = p.get("grade", "?")
    action = p.get("action", "")
    rationale = p.get("rationale", "")
    warning = p.get("warning_text", "")
    values = p.get("values") or {}
    nums = ", ".join(f"{k}={v}" for k, v in values.items())
    body = " ".join(s for s in (str(action), str(rationale), nums) if s).strip()
    if language == "hi":
        out = f"ग्रेड {grade}। {body}".strip()
    else:
        out = f"Grade {grade}. {body}".strip()
    return f"{warning} {out}".strip() if warning else out


def phrase(advisory: dict, forecast: dict, warning: dict, confidence: dict, location: dict, lang: str) -> str:
    advice = advisory.get("advice_hi") if lang == "hi" else advisory.get("advice_en")
    return (
        f"{location['name']}: {forecast['temp_c']}C, {forecast['condition']}. "
        f"Warning: {_warn_state(warning)}. Agreement: {confidence['grade']}. Advice: {advice}"
    )
