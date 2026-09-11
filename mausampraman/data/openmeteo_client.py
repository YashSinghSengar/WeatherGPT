"""Real Open-Meteo client. Frozen contract, see CONTRACTS.md."""
from datetime import datetime, timezone

import httpx

MODELS = ("gfs_seamless", "ecmwf_ifs025", "icon_seamless")
URL = "https://api.open-meteo.com/v1/forecast"


class DataUnavailable(Exception):
    pass


def _current_index(times: list) -> int:
    try:
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        key = now.strftime("%Y-%m-%dT%H:00")
        return times.index(key)
    except Exception:
        return 0


def get_forecast(lat: float, lon: float) -> dict:
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
        return {
            "temp_c": round(temp_c, 1),
            "humidity_pct": 0,  # ponytail: not requested from API, neutral until wired
            "wind_kph": 0.0,  # ponytail: not requested from API, neutral until wired
            "precip_mm": round(precip_mm, 1),
            "condition": "rain" if precip_mm >= 0.5 else "partly_cloudy",
            "source": "openmeteo",
            "lat": lat,
            "lon": lon,
        }
    except DataUnavailable:
        raise
    except Exception as e:
        raise DataUnavailable(str(e)) from e


def get_divergence_scenario(forecast: dict | None = None) -> dict:
    return {"spread_c": 0.5, "scenario": "low_spread_stub", "source": "stub"}
