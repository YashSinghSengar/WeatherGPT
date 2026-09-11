"""Deterministic templates. Only wording layer."""


def phrase(advisory: dict, forecast: dict, warning: dict, confidence: dict, location: dict, lang: str) -> str:
    advice = advisory.get("advice_hi") if lang == "hi" else advisory.get("advice_en")
    return (
        f"{location['name']}: {forecast['temp_c']}C, {forecast['condition']}. "
        f"Warning: {warning['level']}. Confidence: {confidence['level']}. Advice: {advice}"
    )
