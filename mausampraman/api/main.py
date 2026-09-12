"""FastAPI entry. Deterministic pipeline, LLM only for wording."""
import sys
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.geocoder import resolve_location
from data.openmeteo_client import default_target_date, divergence_scenario_from_models, get_forecast, prevruns_per_model
from data.warning_store import get_warning
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


def _compose(intent: str, location: dict, forecast: dict, warning: dict, confidence: dict) -> str:
    sev, grade = warning.get("severity", "green"), confidence.get("grade", "?")
    if intent == "warning_status":
        return f"{location['name']}: warning {sev}. {warning.get('headline', '')} Agreement {grade}."
    if intent == "forecast_rain":
        return f"{location['name']}: {forecast.get('precip_mm')}mm rain expected. Warning: {sev}. Agreement {grade}."
    if intent == "confidence_explanation":
        return f"{location['name']}: agreement {grade} from model spread {confidence.get('spread_mm')}mm, not a probability. Warning: {sev}."
    return f"{location['name']}: {forecast.get('temp_c')}C, {forecast.get('condition')}. Warning: {sev}. Agreement {grade}."


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
        }
    if intent["intent"] == "unsupported":
        intent = {"intent": "weather_current", "confidence": "high", "signals": ["location-only"]}
    res = resolve_location(body.query, body.location)
    if res is None:
        raise HTTPException(status_code=404, detail="could not determine location from query")
    place, lat, lon = res
    location = {"name": place, "lat": lat, "lon": lon, "state": "Unknown", "country": "Unknown"}
    forecast = get_forecast(lat, lon)
    district = location["name"].split()[0].lower()  # ponytail: first-token match, real district resolve later
    warning = get_warning(district) or {
        "district": district,
        "severity": "green",
        "headline": "No warning",
        "body": "",
        "issued_at": date.today().isoformat(),
        "capture_date": date.today().isoformat(),
    }
    per_model = prevruns_per_model(lat, lon, default_target_date())  # single fetch, shared below
    divergence = divergence_scenario_from_models(lat, lon, per_model)
    confidence = grade_forecast(forecast, warning, divergence, per_model)  # deterministic, LLM never touches
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
    }
