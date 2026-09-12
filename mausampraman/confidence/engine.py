"""Deterministic confidence engine. LLM must never override this."""
import json
import time

from data.openmeteo_client import _cache_path, default_target_date, prevruns_per_model

SKILL_PRIOR = {}  # ponytail: empty until verification history exists; lookup recorded only
HORIZON_DAYS = 2  # ponytail: mirrors forecast_days in openmeteo_client


def model_spread(models: dict) -> float:
    rains = [v["rain_mm"] for v in models.values()]
    return max(rains) - min(rains)


def feed_age_minutes(lat: float, lon: float) -> float:
    try:
        fetched = float(json.loads(_cache_path(lat, lon).read_text()).get("fetched_at", 0))
        if fetched:
            return max(0.0, (time.time() - fetched) / 60)
    except Exception:
        pass
    return 0.0  # ponytail: just fetched, write failed; age ~0


def grade(models: dict, warning: dict | None, feed_age_min: float, horizon_days: int) -> dict:
    if isinstance(models.get("models"), dict):
        models = models["models"]  # ponytail: accept wrapped or flat models dict
    spread = round(model_spread(models), 1)
    prior = SKILL_PRIOR.get("default", 0.0)
    drivers = {"spread_mm": spread}
    if warning and warning.get("severity", "green") != "green":
        return {"grade": "D", "warning_override": True, "spread_mm": spread, "skill_prior": prior, "drivers": drivers}
    if spread < 5 and feed_age_min < 90 and horizon_days <= 2:
        band = "A"
    elif spread < 15 and feed_age_min < 180 and horizon_days <= 3:
        band = "B"
    elif spread < 25 and horizon_days <= 5:
        band = "C"
    else:
        band = "D"
    return {"grade": band, "warning_override": False, "spread_mm": spread, "skill_prior": prior, "drivers": drivers}


def grade_forecast(forecast: dict, warning: dict, divergence: dict, models: dict | None = None) -> dict:
    lat, lon = forecast.get("lat"), forecast.get("lon")
    if models is None:  # ponytail: back-compat fetch; pipeline passes models to avoid duplicate call
        models = prevruns_per_model(lat, lon, default_target_date())
    return grade(models, warning, feed_age_minutes(lat, lon), HORIZON_DAYS)
