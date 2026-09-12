"""Deterministic intent classifier. Keywords only, no LLM, no location logic."""

GROUPS = [
    ("warning_status", {"warning", "warnings", "warned", "alert", "alerts", "cyclone", "flood", "chetawani", "khatra", "toofan", "aandhi", "चेतावनी", "खतरा", "तूफान", "आंधी", "बाढ़"}),
    ("agriculture_advice", {"irrigate", "irrigation", "spray", "fertil", "pesticide", "fungicide", "harvest", "sow", "sowing", "prune", "crop", "fasal", "sinchai", "chhidkav", "khad", "katai", "grape", "angoor", "फसल", "सिंचाई", "छिड़काव", "खाद", "कटाई", "अंगूर", "बुवाई"}),
    ("confidence_explanation", {"why", "kyon", "confidence", "confident", "trust", "grade", "bharosa", "sure", "certain", "क्यों", "भरोसा", "विश्वास"}),
    ("forecast_rain", {"rain", "rains", "rainy", "precip", "shower", "drizzle", "baarish", "barsaat", "geela", "बारिश", "बरसात"}),
    ("weather_current", {"weather", "mausam", "temperature", "temp", "tapman", "hot", "cold", "humid", "wind", "cloud", "sunny", "forecast", "condition", "मौसम", "तापमान", "गर्मी", "सर्दी", "हवा", "बादल", "धूप"}),
]


def classify_intent(query: str) -> dict:
    text = (query or "").lower()
    hits = []
    for intent, words in GROUPS:
        found = sorted({w for w in words if w in text})
        if found:
            hits.append((intent, found))
    if not hits:
        return {"intent": "unsupported", "confidence": "high", "signals": []}
    intent, signals = hits[0]
    return {"intent": intent, "confidence": "high" if len(hits) == 1 else "medium", "signals": signals}
