"""Evidence builder. Pure projection of retrieved data, no external calls.

Evidence records what the backend already knows and where it came from.
Missing metadata stays None, never invented.
"""

MODEL_NAMES = {"gfs_seamless": "GFS", "ecmwf_ifs025": "ECMWF", "icon_seamless": "ICON"}


def build_evidence(location=None, forecast=None, per_model=None, confidence=None,
                   warning=None, advisory_status=None, advisory=None,
                   crop=None, stage=None) -> dict:
    """Structured evidence from objects already in hand."""
    location = location or {}
    forecast = forecast or {}
    confidence = confidence or {}
    warning = warning or {}
    per_model = per_model or {}
    values = {}
    for canon, legacy in (("temperature", "temp_c"), ("precipitation", "precip_mm"),
                          ("precipitation_probability", "precip_prob_pct"), ("humidity", "humidity_pct"),
                          ("wind_speed", "wind_kph"), ("weather_code", "weather_code"),
                          ("condition", "condition")):
        if forecast.get(legacy) is not None:
            values[canon] = forecast.get(legacy)
    return {
        "location": {
            "display_name": location.get("name"),
            "latitude": location.get("lat"),
            "longitude": location.get("lon"),
            "state": location.get("state"),
            "district": location.get("district"),
        },
        "weather": {
            "source": forecast.get("source"),
            "models": sorted({MODEL_NAMES.get(m, m) for m in per_model}),
            "retrieved_at": None,  # legacy forecast view carries no retrieval stamp
            "forecast_time": forecast.get("observed_at"),
            "values": values,
        },
        "agreement": {
            "grade": confidence.get("grade"),
            "models_considered": sorted({MODEL_NAMES.get(m, m) for m in per_model}),
            "basis": {"spread_mm": confidence.get("spread_mm"),
                      "warning_override": confidence.get("warning_override"),
                      "drivers": confidence.get("drivers")},
        },
        "warning": {
            "state": warning.get("status", warning.get("state")),
            "severity": warning.get("severity"),
            "source": warning.get("source", "warnings-store"),
            "headline": warning.get("headline"),
            "issued_at": warning.get("issued_at"),
            "valid_until": warning.get("valid_until"),
        },
        "advisory": {
            "status": advisory_status,
            "rule_id": (advisory or {}).get("rule_id"),
            "source": (advisory or {}).get("source"),
            "citation": (advisory or {}).get("citation"),
            "crop": crop,
            "stage": stage,
        },
    }
