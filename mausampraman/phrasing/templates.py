"""Deterministic templates. Only wording layer."""


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
        f"Warning: {warning.get('severity', 'green')}. Confidence: {confidence['grade']}. Advice: {advice}"
    )
