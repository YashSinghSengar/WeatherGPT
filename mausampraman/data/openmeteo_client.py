"""Real Open-Meteo client. Frozen contract, see CONTRACTS.md."""
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

MODELS = ("gfs_seamless", "ecmwf_ifs025", "icon_seamless")
URL = "https://api.open-meteo.com/v1/forecast"
PREV_URL = "https://previous-runs-api.open-meteo.com/v1/forecast"
CACHE_DIR = Path(__file__).parent / ".cache"
CACHE_TTL_S = 30 * 60


class DataUnavailable(Exception):
    pass


def _current_index(times: list) -> int:
    try:
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        key = now.strftime("%Y-%m-%dT%H:00")
        return times.index(key)
    except Exception:
        return 0


def _cache_path(lat: float, lon: float) -> Path:
    hour = datetime.now(timezone.utc).strftime("%Y%m%d%H")
    return CACHE_DIR / f"forecast_{lat}_{lon}_{hour}.json"


def _cache_hit(path: Path) -> dict | None:
    try:
        cached = json.loads(path.read_text())
        if time.time() - float(cached.get("fetched_at", 0)) < CACHE_TTL_S:
            cached.pop("fetched_at", None)
            return cached
    except Exception:
        pass
    return None


def get_forecast(lat: float, lon: float) -> dict:
    path = _cache_path(lat, lon)
    if path.exists():
        hit = _cache_hit(path)
        if hit is not None:
            return hit
    try:
        r = httpx.get(
            URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "rain,temperature_2m",
                "models": ",".join(MODELS),
                "forecast_days": 2,
            },
            timeout=10.0,
        )
        r.raise_for_status()
        hourly = r.json().get("hourly", {})
        times = hourly.get("time", [])
        if not times:
            raise ValueError("empty hourly time")
        idx = _current_index(times)
        # Next-day = latest date in response (forecast_days=2, second day)
        next_day = max(t[:10] for t in times)
        temps, rains = [], []
        for m in MODELS:
            tvals = hourly.get(f"temperature_2m_{m}") or hourly.get("temperature_2m")
            rvals = hourly.get(f"rain_{m}") or hourly.get("rain")
            if not tvals or not rvals:
                raise ValueError(f"missing model {m}")
            temps.append(float(tvals[idx]))
            rains.append(sum(float(v) for t, v in zip(times, rvals) if t[:10] == next_day))
        temp_c = sum(temps) / len(temps)
        precip_mm = sum(rains) / len(rains)
        result = {
            "temp_c": round(temp_c, 1),
            "humidity_pct": 0,  # ponytail: not requested from API, neutral until wired
            "wind_kph": 0.0,  # ponytail: not requested from API, neutral until wired
            "precip_mm": round(precip_mm, 1),
            "condition": "rain" if precip_mm >= 0.5 else "partly_cloudy",
            "source": "openmeteo",
            "lat": lat,
            "lon": lon,
        }
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({**result, "fetched_at": time.time()}))
        except Exception:
            pass
        return result
    except DataUnavailable:
        raise
    except Exception as e:
        raise DataUnavailable(str(e)) from e


def get_divergence_scenario(lat: float, lon: float, target_date: str | None = None) -> dict:
    if target_date is None:
        target_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    per = prevruns_per_model(lat, lon, target_date)
    temps = [v["temp_c"] for v in per.values()]
    rains = [v["rain_mm"] for v in per.values()]
    temp_c = sum(temps) / len(temps)
    precip_mm = sum(rains) / len(rains)
    return {
        "temp_c": round(temp_c, 1),
        "humidity_pct": 0,  # ponytail: not requested from API, neutral until wired
        "wind_kph": 0.0,  # ponytail: not requested from API, neutral until wired
        "precip_mm": round(precip_mm, 1),
        "condition": "rain" if precip_mm >= 0.5 else "partly_cloudy",
        "source": "openmeteo-prevruns",
        "lat": lat,
        "lon": lon,
    }


def prevruns_per_model(lat: float, lon: float, date_str: str) -> dict:
    """Per-model {temp_c daily mean, rain_mm daily total} for one past date."""
    try:
        r = httpx.get(
            PREV_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "rain,temperature_2m",
                "models": ",".join(MODELS),
                "start_date": date_str,
                "end_date": date_str,
            },
            timeout=10.0,
        )
        r.raise_for_status()
        hourly = r.json().get("hourly", {})
        times = hourly.get("time", [])
        if not times:
            raise ValueError("empty hourly time")
        out = {}
        for m in MODELS:
            tvals = hourly.get(f"temperature_2m_{m}") or hourly.get("temperature_2m")
            rvals = hourly.get(f"rain_{m}") or hourly.get("rain")
            if not tvals or not rvals:
                raise ValueError(f"missing model {m}")
            day_t = [float(v) for t, v in zip(times, tvals) if t[:10] == date_str]
            day_r = [float(v) for t, v in zip(times, rvals) if t[:10] == date_str]
            if not day_t:
                raise ValueError(f"no hours for {date_str}")
            out[m] = {"temp_c": round(sum(day_t) / len(day_t), 1), "rain_mm": round(sum(day_r), 1)}
        return out
    except DataUnavailable:
        raise
    except Exception as e:
        raise DataUnavailable(str(e)) from e
