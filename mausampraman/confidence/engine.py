"""Deterministic confidence engine. LLM must never override this."""
# ponytail: rule stub, real scoring later


def grade(forecast: dict, warning: dict, divergence: dict) -> dict:
    reasons = ["stub-grade"]
    level = "MEDIUM"
    if warning.get("level") != "none":
        level = "LOW"
        reasons.append("active-warning")
    elif divergence.get("spread_c", 0) <= 1.0:
        level = "HIGH"
        reasons.append("low-spread")
    return {"level": level, "reasons": reasons, "scores": {"spread_c": divergence.get("spread_c", 0)}}
