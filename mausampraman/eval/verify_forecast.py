"""Historical forecast verification machinery. Stdlib only.

Record schema (one JSON object per line):
  location, lat, lon, forecast_time (ISO), target_date (YYYY-MM-DD),
  horizon_days (int), model (str), predicted_precip_mm (float),
  observed_precip_mm (float | null), absolute_error (float | null)

OBSERVATION_INGESTION_AVAILABLE = False: no reliable observation
source is wired yet (candidate: Open-Meteo ERA5/archive API).
Until then, observed_* stays null outside clearly-labeled test
fixtures. Nothing here is a real-world result.
"""

import json
from pathlib import Path
from statistics import mean

OBSERVATION_INGESTION_AVAILABLE = False
REQUIRED = ("location", "lat", "lon", "forecast_time", "target_date", "horizon_days", "model", "predicted_precip_mm")


def append_forecast(path: str | Path, *, location: str, lat: float, lon: float, forecast_time: str, target_date: str, horizon_days: int, model: str, predicted_precip_mm: float) -> dict:
    rec = {"location": location, "lat": lat, "lon": lon, "forecast_time": forecast_time, "target_date": target_date,
           "horizon_days": horizon_days, "model": model, "predicted_precip_mm": predicted_precip_mm,
           "observed_precip_mm": None, "absolute_error": None}
    with open(path, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def append_observation(path: str | Path, *, location: str, target_date: str, model: str, observed_precip_mm: float) -> int:
    p = Path(path)
    if not p.exists():
        return 0
    n, out = 0, []
    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("location") == location and rec.get("target_date") == target_date and rec.get("model") == model and rec.get("observed_precip_mm") is None:
            rec["observed_precip_mm"] = observed_precip_mm
            rec["absolute_error"] = round(abs(rec["predicted_precip_mm"] - observed_precip_mm), 1)
            n += 1
        out.append(rec)
    p.write_text("".join(json.dumps(r) + "\n" for r in out))
    return n


def load(path: str | Path) -> list:
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def _mae(recs: list) -> dict:
    errs = [r["absolute_error"] for r in recs if r.get("absolute_error") is not None]
    return {"n": len(errs), "mae": round(mean(errs), 2) if errs else None}


def metrics(records: list) -> dict:
    by = lambda key: {k: _mae([r for r in records if r.get(key) == k]) for k in sorted({r.get(key) for r in records})}
    return {"samples": _mae(records), "by_model": by("model"), "by_horizon": by("horizon_days"), "by_location": by("location")}


if __name__ == "__main__":
    import sys
    print(json.dumps(metrics(load(sys.argv[1])), indent=2))
