"""FastAPI entry. Deterministic pipeline, LLM only for wording."""
import sys
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.geocoder import geocode
from data.openmeteo_client import get_divergence_scenario, get_forecast
from data.warning_store import get_warning
from confidence.engine import grade_forecast
from confidence.grounding import ground_check
from advisory.engine import get_advisory
from phrasing.templates import phrase

app = FastAPI(title="MausamPraman")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class AskIn(BaseModel):
    query: str = "Nashik weather"
    lang: str = "en"
    crop: str = "grape"
    stage: str = "veraison"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(body: AskIn):
    lang = body.lang if body.lang in ("en", "hi") else "en"
    coords = geocode(body.query)
    if coords is None:
        raise HTTPException(status_code=404, detail="location not found")
    lat, lon = coords
    location = {"name": (body.query or "").strip() or "Unknown", "lat": lat, "lon": lon, "state": "Unknown", "country": "Unknown"}
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
    divergence = get_divergence_scenario(lat, lon)
    confidence = grade_forecast(forecast, warning, divergence)  # deterministic, LLM never touches
    advisory = get_advisory(body.crop, body.stage, confidence)
    if advisory is None:
        raise HTTPException(status_code=400, detail="no advisory rule for crop/stage")
    answer = phrase(advisory, forecast, warning, confidence, location, lang)  # wording only
    check = ground_check(answer, forecast, warning)
    return {
        "answer": answer,
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
