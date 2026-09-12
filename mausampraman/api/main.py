"""FastAPI entry. Deterministic pipeline, LLM only for wording."""
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.geocoder import resolve_location
from data.openmeteo_client import DataUnavailable, default_target_date, divergence_scenario_from_models, get_daily, get_forecast, prevruns_per_model
from data.warning_store import STATUS_TEXT, get_warning
from confidence.engine import grade_forecast
from confidence.grounding import ground_check
from advisory.engine import get_advisory
from phrasing.templates import phrase
from api.intent import classify_intent

app = FastAPI(title="MausamPraman")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskIn(BaseModel):
    query: str = "Nashik weather"
    lang: str = "en"
    language: str | None = None
    location: str | None = None
    crop: str | None = None
    stage: str | None = None


CROPS = {"grape": ("grape", "angoor", "अंगूर")}
STAGES = ("flowering", "fruit-set", "fruitset", "veraison", "harvest")


def _resolve_crop_stage(query: str, crop: str | None, stage: str | None) -> tuple[str | None, str | None]:
    q = (query or "").lower()
    if crop is None:
        for name, words in CROPS.items():
            if any(w in q for w in words):
                crop = name
                break
    if stage is None:
        for s in STAGES:
            if s in q:
                stage = "fruit-set" if s == "fruitset" else s
                break
    return crop, stage


@app.get("/health")
def health():
    return {"status": "ok"}


def _warn_state(warning: dict) -> str:
    sev = warning.get("severity", "green")
    return sev if warning.get("status") == "active_warning" else STATUS_TEXT.get(warning.get("status", ""), sev)


def _compose(intent: str, location: dict, forecast: dict, warning: dict, confidence: dict) -> str:
    sev, grade = _warn_state(warning), confidence.get("grade", "?")
    wlabel = f"Warning: {sev}" if warning.get("status") == "active_warning" else sev
    if intent == "warning_status":
        return f"{location['name']}: {wlabel}. {warning.get('headline', '')} Agreement {grade}."
    if intent == "forecast_rain":
        return f"{location['name']}: {forecast.get('precip_mm')}mm rain expected. {wlabel}. Agreement {grade}."
    if intent == "confidence_explanation":
        spread = confidence.get("spread_mm")
        spread_txt = f"{spread}mm" if isinstance(spread, (int, float)) else "unknown"
        return f"{location['name']}: agreement {grade} from model spread {spread_txt}, not a probability. {wlabel}."
    return f"{location['name']}: {forecast.get('temp_c')}C, {forecast.get('condition')}. {wlabel}. Agreement {grade}."


@app.post("/ask")
def ask(body: AskIn):
    lang = body.language or body.lang
    lang = lang if lang in ("en", "hi") else "en"
    intent = classify_intent(body.query)
    if intent["intent"] == "unsupported" and resolve_location(body.query, body.location) is None:
        return {
            "answer": "I can help with current weather, rain forecasts, warnings, grape advice, or forecast trust. Please ask about a place.",
            "intent": intent,
            "confidence": None,
            "provenance": {"forecast_source": "none", "warning_source": "warnings-store", "grounded": True},
            "advisory": None,
            "location": None,
            "warning": None,
            "forecast": None,
            "daily": None,
        }
    if intent["intent"] == "unsupported":
        intent = {"intent": "weather_current", "confidence": "high", "signals": ["location-only"]}
    try:
        res = resolve_location(body.query, body.location)
    except DataUnavailable:
        raise HTTPException(status_code=503, detail="location service temporarily unavailable")
    if res is None:
        raise HTTPException(status_code=404, detail="could not determine location from query")
    place, lat, lon = res
    location = {"name": place, "lat": lat, "lon": lon, "state": "Unknown", "country": "Unknown"}
    try:
        forecast = get_forecast(lat, lon)
    except DataUnavailable:
        raise HTTPException(status_code=503, detail="weather data temporarily unavailable")
    district = location["name"].split()[0].lower()  # ponytail: first-token match, real district resolve later
    try:
        warning = get_warning(district)
    except Exception:
        warning = {"district": district, "severity": "green", "headline": "Warning status unavailable", "body": "",
                   "issued_at": "", "capture_date": "", "status": "warning_data_unavailable"}
    try:
        per_model = prevruns_per_model(lat, lon, default_target_date())  # single fetch, shared below
        divergence = divergence_scenario_from_models(lat, lon, per_model)
        confidence = grade_forecast(forecast, warning, divergence, per_model)  # deterministic, LLM never touches
    except DataUnavailable:
        overridden = warning.get("severity", "green") != "green"
        divergence = None
        confidence = {"grade": "D", "warning_override": overridden, "spread_mm": None, "skill_prior": 0.0,
                      "drivers": {"spread_mm": None}, "reasons": ["divergence-unavailable"] + (["active-warning"] if overridden else [])}
    try:
        daily = get_daily(lat, lon)
    except DataUnavailable:
        daily = None
    advisory = None
    if intent["intent"] == "agriculture_advice":
        crop, stage = _resolve_crop_stage(body.query, body.crop, body.stage)
        if crop is not None and stage is not None:
            advisory = get_advisory(crop, stage, confidence)
        if advisory is None:
            return {
                "answer": f"Specific grounded guidance for {crop or 'this crop'}/{stage or 'this stage'} is unavailable.",
                "intent": intent,
                "confidence": confidence,
                "provenance": {"forecast_source": forecast["source"], "warning_source": "warnings-store", "grounded": True},
                "advisory": None,
                "location": location,
                "warning": warning,
                "forecast": forecast,
                "daily": daily,
            }
        answer = phrase(advisory, forecast, warning, confidence, location, lang)  # wording only
    else:
        answer = _compose(intent["intent"], location, forecast, warning, confidence)
    check = ground_check(answer, forecast, warning, confidence, advisory, location)
    return {
        "answer": answer,
        "intent": intent,
        "confidence": confidence,
        "provenance": {
            "forecast_source": forecast["source"],
            "warning_source": "warnings-store",
            "grounded": check["grounded"],
        },
        "advisory": advisory,
        "location": location,
        "warning": warning,
        "forecast": forecast,
        "daily": daily,
    }
