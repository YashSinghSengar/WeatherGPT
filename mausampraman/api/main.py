"""FastAPI entry. Deterministic pipeline, LLM only for wording."""
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.geocoder import geocode
from data.openmeteo_client import get_divergence_scenario, get_forecast
from data.warning_store import get_warning
from confidence.engine import grade
from confidence.grounding import ground_check
from advisory.engine import get_advisory
from phrasing.templates import phrase

app = FastAPI(title="MausamPraman")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class AskIn(BaseModel):
    query: str = "Nashik weather"
    lang: str = "en"
    crop: str = "grape"


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
    warning = get_warning(lat, lon)
    divergence = get_divergence_scenario(forecast)
    confidence = grade(forecast, warning, divergence)  # deterministic, LLM never touches
    advisory = get_advisory(body.crop, forecast, warning, confidence)
    answer = phrase(advisory, forecast, warning, confidence, location, lang)  # wording only
    check = ground_check(answer, forecast, warning)
    return {
        "answer": answer,
        "confidence": confidence,
        "provenance": {
            "forecast_source": forecast["source"],
            "warning_source": warning["source"],
            "grounded": check["grounded"],
        },
        "advisory": advisory,
        "location": location,
        "warning": warning,
        "forecast": forecast,
    }
