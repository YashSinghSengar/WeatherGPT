"""FastAPI entry. Deterministic pipeline, LLM only for wording."""
import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.geocoder import resolve_canonical
from data.openmeteo_client import DataUnavailable, default_target_date, divergence_scenario_from_models, get_daily, get_forecast, prevruns_per_model
from data.warning_store import STATUS_TEXT, get_warning
from confidence.engine import grade_forecast
from confidence.grounding import ground_check
from advisory.engine import get_advisory
from phrasing.templates import phrase
from api.intent import classify_intent

app = FastAPI(title="MausamPraman")
log = logging.getLogger("mausampraman")
if not log.handlers:  # ponytail: stdout JSON lines even without uvicorn handlers
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(_h)
log.setLevel(logging.INFO)


def allowed_origins() -> list:
    prod = os.environ.get("FRONTEND_ORIGIN", "").strip()
    if prod:
        return [prod]
    return ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
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
def ask(body: AskIn, response: Response):
    rid = uuid.uuid4().hex[:12]
    t0 = time.perf_counter()

    def emit(status: int, **kw) -> None:
        rec = {"request_id": rid, "duration_ms": round((time.perf_counter() - t0) * 1000, 1),
               "status": status, "wording": "template", **kw}
        response.headers["X-Request-ID"] = rid
        log.info(json.dumps(rec))

    def fail(status: int, detail: str, **kw):
        emit(status, **kw)
        raise HTTPException(status_code=status, detail=detail, headers={"X-Request-ID": rid})

    lang = body.language or body.lang
    lang = lang if lang in ("en", "hi") else "en"
    intent = classify_intent(body.query)
    if intent["intent"] == "unsupported" and resolve_canonical(body.query, body.location) is None:
        emit(200, intent=intent["intent"], location=None, path="unsupported", grade=None, upstream_failure=None)
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
        canon = resolve_canonical(body.query, body.location)
    except DataUnavailable:
        fail(503, "location service temporarily unavailable", intent=intent["intent"], location=None, path="resolve", grade=None, upstream_failure="geocoder")
    if canon is None:
        fail(404, "could not determine location from query", intent=intent["intent"], location=None, path="resolve", grade=None, upstream_failure=None)
    place, lat, lon = canon["name"], canon["latitude"], canon["longitude"]
    location = {"name": place, "lat": lat, "lon": lon, "state": canon.get("state") or "Unknown",
                "country": canon.get("country") or "Unknown", "district": canon.get("district") or place,
                "source": canon.get("source") or "openmeteo-geocoding"}
    try:
        forecast = get_forecast(lat, lon)
    except DataUnavailable:
        fail(503, "weather data temporarily unavailable", intent=intent["intent"], location=place, path="forecast", grade=None, upstream_failure="forecast")
    district = location["name"].split()[0].lower()  # ponytail: first-token match, real district resolve later
    upstream = None
    try:
        warning = get_warning(district)
    except Exception:
        upstream = "warning_store"
        warning = {"district": district, "severity": "green", "headline": "Warning status unavailable", "body": "",
                   "issued_at": "", "capture_date": "", "status": "warning_data_unavailable"}
    try:
        per_model = prevruns_per_model(lat, lon, default_target_date())  # single fetch, shared below
        divergence = divergence_scenario_from_models(lat, lon, per_model)
        confidence = grade_forecast(forecast, warning, divergence, per_model)  # deterministic, LLM never touches
    except DataUnavailable:
        upstream = "divergence"
        overridden = warning.get("severity", "green") != "green"
        divergence = None
        confidence = {"grade": "D", "warning_override": overridden, "spread_mm": None, "skill_prior": 0.0,
                      "drivers": {"spread_mm": None}, "reasons": ["divergence-unavailable"] + (["active-warning"] if overridden else [])}
    try:
        daily = get_daily(lat, lon)
    except DataUnavailable:
        upstream = upstream or "daily"
        daily = None
    advisory = None
    if intent["intent"] == "agriculture_advice":
        crop, stage = _resolve_crop_stage(body.query, body.crop, body.stage)
        if crop is not None and stage is not None:
            advisory = get_advisory(crop, stage, confidence)
        if advisory is None:
            emit(200, intent=intent["intent"], location=place, path="agriculture_advice:unavailable", grade=confidence.get("grade"), upstream_failure=upstream)
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
    emit(200, intent=intent["intent"], location=place, path=intent["intent"], grade=confidence.get("grade"), upstream_failure=upstream)
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
