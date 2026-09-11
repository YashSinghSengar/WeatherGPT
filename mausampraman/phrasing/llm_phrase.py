"""Optional LLM wording hook. Must never change facts/confidence/warnings."""
from .templates import phrase
# ponytail: passthrough stub, real Groq call later behind env flag


def llm_phrase(advisory: dict, forecast: dict, warning: dict, confidence: dict, location: dict, lang: str) -> str:
    return phrase(advisory, forecast, warning, confidence, location, lang)
