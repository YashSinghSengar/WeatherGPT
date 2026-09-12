import data.openmeteo_client as OC

HOURS = [f"2026-09-11T{h:02d}:00" for h in range(24)] + [f"2026-09-12T{h:02d}:00" for h in range(24)]


class _Resp:
    def __init__(self, hourly):
        self._h = hourly
    def raise_for_status(self):
        pass
    def json(self):
        return {"hourly": self._h}


def test_all_fields_preserved(monkeypatch):
    hourly = {"time": HOURS}
    for m, vals in (("gfs_seamless", (20.0, 0.0, 80, 10, 2, 5.0)),
                    ("ecmwf_ifs025", (22.0, 0.0, 90, 20, 2, 7.0)),
                    ("icon_seamless", (21.0, 0.0, 85, 30, 61, 6.0))):
        t, r, h, p, c, w = vals
        hourly.update({f"temperature_2m_{m}": [t] * 48, f"rain_{m}": [r] * 48,
                       f"relative_humidity_2m_{m}": [h] * 48, f"precipitation_probability_{m}": [p] * 48,
                       f"weather_code_{m}": [c] * 48, f"wind_speed_10m_{m}": [w] * 48})
    monkeypatch.setattr(OC.httpx, "get", lambda *a, **k: _Resp(hourly))
    monkeypatch.setattr(OC, "_cache_path", lambda lat, lon: OC.Path("/nonexistent-cache.json"))
    f = OC.get_forecast(1.0, 2.0)
    assert f["temp_c"] == 21.0 and f["humidity_pct"] == 85 and f["precip_prob_pct"] == 20
    assert f["wind_kph"] == round(6.0 * 3.6, 1) and f["weather_code"] == 2
    assert f["condition"] == "partly_cloudy" and f["observed_at"] in HOURS and f["precip_mm"] == 0.0


def test_missing_fields_null_not_zero(monkeypatch):
    hourly = {"time": HOURS}
    for m in ("gfs_seamless", "ecmwf_ifs025", "icon_seamless"):
        hourly.update({f"temperature_2m_{m}": [20.0] * 48, f"rain_{m}": [1.0] * 48})
    monkeypatch.setattr(OC.httpx, "get", lambda *a, **k: _Resp(hourly))
    monkeypatch.setattr(OC, "_cache_path", lambda lat, lon: OC.Path("/nonexistent-cache.json"))
    f = OC.get_forecast(1.0, 2.0)
    assert f["humidity_pct"] is None and f["wind_kph"] is None and f["precip_prob_pct"] is None
    assert f["weather_code"] is None and f["condition"] == "rain"  # precip fallback only here
