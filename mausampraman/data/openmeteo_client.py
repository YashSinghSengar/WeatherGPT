"""Real Open-Meteo client. Frozen contract, see CONTRACTS.md."""
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

from .canonical import canonical_weather

MODELS = ("gfs_seamless", "ecmwf_ifs025", "icon_seamless")
TIMEOUT = 5.0  # ponytail: chat-appropriate per-call bound, no retries anywhere
URL = "https://api.open-meteo.com/v1/forecast"
PREV_URL = "https://previous-runs-api.open-meteo.com/v1/forecast"
HOURLY = "temperature_2m,rain,relative_humidity_2m,precipitation_probability,weather_code,wind_speed_10m"
CACHE_DIR = Path(__file__).parent / ".cache"
CACHE_TTL_S = 30 * 60

WMO = {0: "clear", 1: "mainly_clear", 2: "partly_cloudy", 3: "overcast", 45: "fog", 48: "fog",
       51: "drizzle", 53: "drizzle", 55: "drizzle", 56: "freezing_drizzle", 57: "freezing_drizzle",
       61: "rain", 63: "rain", 65: "rain", 66: "freezing_rain", 67: "freezing_rain",
       71: "snow", 73: "snow", 75: "snow", 77: "snow_grains",
       80: "showers", 81: "showers", 82: "showers", 85: "snow_showers", 86: "snow_showers",
       95: "thunderstorm", 96: "thunderstorm_hail", 99: "thunderstorm_hail"}


def _modal_code(codes: list) -> int | None:
    codes = [c for c in codes if c is not None]
    return max(set(codes), key=codes.count) if codes else None


def _condition(code: int | None, precip_mm: float) -> str:
    if code is None:  # actual fallback only when weather-code data missing
        return "rain" if precip_mm >= 0.5 else "partly_cloudy"
    return WMO.get(code, "unknown")


class DataUnavailable(Exception):
    pass


class ProviderTimeout(DataUnavailable):
    """Upstream did not answer in time. Never fabricated, never substituted."""


class ProviderHTTPError(DataUnavailable):
    """Upstream answered with HTTP failure."""


class ProviderMalformed(DataUnavailable):
    """Upstream payload could not be parsed."""


def _provider_error(e: Exception) -> DataUnavailable:
    if isinstance(e, httpx.TimeoutException):
        return ProviderTimeout(str(e))
    if isinstance(e, httpx.HTTPError):
        return ProviderHTTPError(str(e))
    if isinstance(e, (ValueError, KeyError, TypeError, IndexError)):
        return ProviderMalformed(str(e))
    return DataUnavailable(str(e))


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
            if "current" in cached and "forecast" in cached:  # ponytail: pre-canonical files miss once, then rewrite
                return cached
    except Exception:
        pass
    return None


def _model_series(hourly: dict, var: str, m: str) -> list | None:
    return hourly.get(f"{var}_{m}") or hourly.get(var)


def _fetch_hourly(lat: float, lon: float) -> tuple[dict, list, int]:
    """Raw hourly payload, times, current-hour index. Raises DataUnavailable."""
    try:
        r = httpx.get(
            URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": HOURLY,
                "models": ",".join(MODELS),
                "forecast_days": 2,
            },
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        hourly = r.json().get("hourly", {})
        times = hourly.get("time", [])
        if not times:
            raise ValueError("empty hourly time")
        return hourly, times, _current_index(times)
    except DataUnavailable:
        raise
    except Exception as e:
        raise _provider_error(e) from e


def _at_idx(hourly: dict, var: str, idx: int, cast) -> list:
    vals = []
    for m in MODELS:
        s = _model_series(hourly, var, m)
        if s is not None and idx < len(s) and s[idx] is not None:
            try:
                vals.append(cast(s[idx]))
            except (TypeError, ValueError):
                pass
    return vals


def _day_vals(hourly: dict, var: str, m: str, times: list, day: str, cast=float) -> list:
    return [cast(v) for t, v in zip(times, _model_series(hourly, var, m) or [])
            if t[:10] == day and v is not None]


def get_canonical_weather(lat: float, lon: float) -> dict:
    """Canonical weather: current separate from forecast[]. Missing stays None."""
    path = _cache_path(lat, lon)
    if path.exists():
        hit = _cache_hit(path)
        if hit is not None:
            return hit
    hourly, times, idx = _fetch_hourly(lat, lon)
    # Next-day = latest date in response (forecast_days=2, second day)
    next_day = max(t[:10] for t in times)
    temps, rains = [], []
    for m in MODELS:
        tvals = _model_series(hourly, "temperature_2m", m)
        rvals = _model_series(hourly, "rain", m)
        if not tvals or not rvals:
            raise ProviderMalformed(f"missing model {m}")
        temps.append(float(tvals[idx]))
        rains.append(sum(float(v) for t, v in zip(times, rvals) if t[:10] == next_day))
    hums = _at_idx(hourly, "relative_humidity_2m", idx, float)
    winds = _at_idx(hourly, "wind_speed_10m", idx, float)
    probs = _at_idx(hourly, "precipitation_probability", idx, float)
    codes = _at_idx(hourly, "weather_code", idx, int)
    code = _modal_code(codes)
    cur_rain = []
    for m in MODELS:
        s = _model_series(hourly, "rain", m)
        if s is not None and idx < len(s) and s[idx] is not None:
            cur_rain.append(float(s[idx]))
    current = {
        "timestamp": times[idx],
        "temperature": round(sum(temps) / len(temps), 1),
        "feels_like": None,  # not requested from provider
        "humidity": round(sum(hums) / len(hums)) if hums else None,
        "precipitation": round(sum(cur_rain) / len(cur_rain), 1) if cur_rain else None,
        "precipitation_probability": round(sum(probs) / len(probs)) if probs else None,
        "wind_speed": round(sum(winds) / len(winds) * 3.6, 1) if winds else None,
        "wind_direction": None,  # not requested from provider
        "weather_code": code,
    }
    days = sorted({t[:10] for t in times})
    periods = []
    for day in days:
        dtemps, draons, dhums, dwinds, dprobs, dcodes = [], [], [], [], [], []
        for m in MODELS:
            dt = _day_vals(hourly, "temperature_2m", m, times, day)
            dr = _day_vals(hourly, "rain", m, times, day)
            if dt:
                dtemps.append(sum(dt) / len(dt))
            if dr:
                draons.append(sum(dr))
            dh = _day_vals(hourly, "relative_humidity_2m", m, times, day)
            if dh:
                dhums.append(sum(dh) / len(dh))
            dw = _day_vals(hourly, "wind_speed_10m", m, times, day)
            if dw:
                dwinds.append(sum(dw) / len(dw) * 3.6)
            dp = _day_vals(hourly, "precipitation_probability", m, times, day)
            if dp:
                dprobs.append(sum(dp) / len(dp))
            dcodes += [int(v) for t, v in zip(times, _model_series(hourly, "weather_code", m) or [])
                       if t[:10] == day and v is not None]
        dcode = _modal_code(dcodes)
        dprecip = round(sum(draons) / len(draons), 1) if draons else None
        periods.append({
            "timestamp": day,
            "temperature": round(sum(dtemps) / len(dtemps), 1) if dtemps else None,
            "precipitation": dprecip,
            "precipitation_probability": round(sum(dprobs) / len(dprobs)) if dprobs else None,
            "humidity": round(sum(dhums) / len(dhums)) if dhums else None,
            "wind_speed": round(sum(dwinds) / len(dwinds), 1) if dwinds else None,
            "wind_direction": None,  # not requested from provider
            "weather_code": dcode,
        })
    result = canonical_weather(lat, lon, current, periods, source="openmeteo")
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({**result, "fetched_at": time.time()}))
    except Exception:
        pass
    return result


def to_legacy_forecast(weather: dict) -> dict:
    """Project canonical back to the frozen /ask forecast shape. Same numbers."""
    cur, lat, lon = weather["current"], weather["location"]["latitude"], weather["location"]["longitude"]
    next_day = max(p["timestamp"] for p in weather["forecast"])
    precip_mm = next(p["precipitation"] for p in weather["forecast"] if p["timestamp"] == next_day)
    code = cur["weather_code"]
    return {
        "temp_c": cur["temperature"],
        "humidity_pct": cur["humidity"],
        "wind_kph": cur["wind_speed"],
        "precip_mm": precip_mm,
        "precip_prob_pct": cur["precipitation_probability"],
        "weather_code": code,
        "condition": _condition(code, precip_mm),
        "observed_at": cur["timestamp"],
        "source": "openmeteo",
        "lat": lat,
        "lon": lon,
    }


def get_forecast(lat: float, lon: float) -> dict:
    path = _cache_path(lat, lon)
    if path.exists():
        hit = _cache_hit(path)
        if hit is not None:
            return to_legacy_forecast(hit)
    try:
        return to_legacy_forecast(get_canonical_weather(lat, lon))
    except DataUnavailable:
        raise
    except Exception as e:
        raise DataUnavailable(str(e)) from e


def default_target_date() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")


def _daily_cache_path(lat: float, lon: float) -> Path:
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    return CACHE_DIR / f"daily_{lat}_{lon}_{day}.json"


def get_daily(lat: float, lon: float, days: int = 3) -> list:
    """Daily periods: date, temp max/min, precip sum, prob max, code. Nulls if absent."""
    path = _daily_cache_path(lat, lon)
    if path.exists():
        try:
            cached = json.loads(path.read_text())
            if time.time() - float(cached.get("fetched_at", 0)) < CACHE_TTL_S:
                return cached["periods"]
        except Exception:
            pass
    try:
        r = httpx.get(
            URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,weathercode",
                "forecast_days": days,
                "timezone": "auto",
            },
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        daily = r.json().get("daily", {})
        dates = daily.get("time", [])
        if not dates:
            raise ValueError("empty daily time")
        out = []
        for i, d in enumerate(dates):
            pick = lambda var: (daily.get(var) or [None])[i] if i < len(daily.get(var) or []) else None
            code = pick("weathercode")
            out.append({
                "date": d,
                "temp_max_c": pick("temperature_2m_max"),
                "temp_min_c": pick("temperature_2m_min"),
                "precip_mm": pick("precipitation_sum"),
                "precip_prob_pct": pick("precipitation_probability_max"),
                "weather_code": code,
                "condition": WMO.get(code, "unknown") if code is not None else None,
            })
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"fetched_at": time.time(), "periods": out}))
        except Exception:
            pass
        return out
    except DataUnavailable:
        raise
    except Exception as e:
        raise _provider_error(e) from e


def divergence_scenario_from_models(lat: float, lon: float, per: dict, observed_at: str | None = None) -> dict:
    """Pure collapse of per-model data to forecast shape. No network."""
    temps = [v["temp_c"] for v in per.values()]
    rains = [v["rain_mm"] for v in per.values()]
    temp_c = sum(temps) / len(temps)
    precip_mm = sum(rains) / len(rains)
    code = _modal_code([v.get("code") for v in per.values()])
    hums = [v["humidity_pct"] for v in per.values() if v.get("humidity_pct") is not None]
    winds = [v["wind_kph"] for v in per.values() if v.get("wind_kph") is not None]
    probs = [v["prob_pct"] for v in per.values() if v.get("prob_pct") is not None]
    return {
        "temp_c": round(temp_c, 1),
        "humidity_pct": round(sum(hums) / len(hums)) if hums else None,
        "wind_kph": round(sum(winds) / len(winds), 1) if winds else None,
        "precip_mm": round(precip_mm, 1),
        "precip_prob_pct": round(sum(probs) / len(probs)) if probs else None,
        "weather_code": code,
        "condition": _condition(code, precip_mm),
        "observed_at": observed_at,
        "source": "openmeteo-prevruns",
        "lat": lat,
        "lon": lon,
    }


def get_divergence_scenario(lat: float, lon: float, target_date: str | None = None) -> dict:
    target_date = target_date or default_target_date()
    return divergence_scenario_from_models(lat, lon, prevruns_per_model(lat, lon, target_date), f"{target_date}T12:00")


def prevruns_per_model(lat: float, lon: float, date_str: str) -> dict:
    """Per-model daily aggregates for one past date."""
    try:
        r = httpx.get(
            PREV_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": HOURLY,
                "models": ",".join(MODELS),
                "start_date": date_str,
                "end_date": date_str,
            },
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        hourly = r.json().get("hourly", {})
        times = hourly.get("time", [])
        if not times:
            raise ValueError("empty hourly time")
        out = {}
        for m in MODELS:
            tvals = _model_series(hourly, "temperature_2m", m)
            rvals = _model_series(hourly, "rain", m)
            if not tvals or not rvals:
                raise ValueError(f"missing model {m}")
            day_t = [float(v) for t, v in zip(times, tvals) if t[:10] == date_str]
            day_r = [float(v) for t, v in zip(times, rvals) if t[:10] == date_str]
            if not day_t:
                raise ValueError(f"no hours for {date_str}")
            rec = {"temp_c": round(sum(day_t) / len(day_t), 1), "rain_mm": round(sum(day_r), 1)}
            hum = _day_mean(hourly, "relative_humidity_2m", m, times, date_str)
            if hum is not None:
                rec["humidity_pct"] = round(hum)
            wind = _day_mean(hourly, "wind_speed_10m", m, times, date_str)
            if wind is not None:
                rec["wind_kph"] = round(wind * 3.6, 1)
            prob = _day_mean(hourly, "precipitation_probability", m, times, date_str)
            if prob is not None:
                rec["prob_pct"] = round(prob)
            codes = [int(v) for t, v in zip(times, _model_series(hourly, "weather_code", m) or []) if t[:10] == date_str and v is not None]
            if codes:
                rec["code"] = _modal_code(codes)
            out[m] = rec
        return out
    except DataUnavailable:
        raise
    except Exception as e:
        raise _provider_error(e) from e


def _day_mean(hourly: dict, var: str, m: str, times: list, date_str: str) -> float | None:
    try:
        vals = [float(v) for t, v in zip(times, _model_series(hourly, var, m) or []) if t[:10] == date_str and v is not None]
        return sum(vals) / len(vals) if vals else None
    except (TypeError, ValueError):
        return None
