"""Deterministic advisory. Reads grape.yaml, no LLM."""
import pathlib
# ponytail: yaml parse without dep, tiny parser for this fixed shape


def _load_rules():
    p = pathlib.Path(__file__).parent / "rules" / "grape.yaml"
    text = p.read_text()
    # Minimal parse: return default rule only for scaffold
    return text


def get_advisory(crop: str, forecast: dict, warning: dict, confidence: dict) -> dict:
    _load_rules()  # ensure file exists, content frozen for now
    temp = forecast.get("temp_c", 0)
    if temp >= 35:
        return {
            "crop": crop,
            "rule_id": "heat_watch",
            "advice_en": "High heat. Irrigate early morning. Avoid pesticide spray midday.",
            "advice_hi": "तेज गर्मी। सुबह सिंचाई करें। दोपहर में छिड़काव न करें।",
            "safe": warning.get("level") == "none",
        }
    return {
        "crop": crop,
        "rule_id": "default",
        "advice_en": "Weather normal for grapes. Maintain routine canopy care.",
        "advice_hi": "अंगूर के लिए मौसम सामान्य। नियमित देखभाल जारी रखें।",
        "safe": warning.get("level") == "none",
    }
