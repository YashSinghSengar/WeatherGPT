import data.openmeteo_client as OC


class _Resp:
    def __init__(self, daily):
        self._d = daily
    def raise_for_status(self):
        pass
    def json(self):
        return {"daily": self._d}


def _daily(**kw):
    base = {"time": ["2026-09-12", "2026-09-13", "2026-09-14"], "temperature_2m_max": [30.0, 31.0, 29.0],
            "temperature_2m_min": [22.0, 23.0, 21.0], "precipitation_sum": [5.0, 0.0, 2.5],
            "precipitation_probability_max": [80, 10, 40], "weathercode": [61, 2, 80]}
    base.update(kw)
    return base


def test_daily_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(OC.httpx, "get", lambda *a, **k: _Resp(_daily()))
    monkeypatch.setattr(OC, "_daily_cache_path", lambda lat, lon: tmp_path / "d.json")
    periods = OC.get_daily(1.0, 2.0)
    assert len(periods) == 3
    assert periods[0] == {"date": "2026-09-12", "temp_max_c": 30.0, "temp_min_c": 22.0, "precip_mm": 5.0,
                          "precip_prob_pct": 80, "weather_code": 61, "condition": "rain"}
    assert periods[1]["condition"] == "partly_cloudy"


def test_daily_nulls_not_zeros(monkeypatch, tmp_path):
    monkeypatch.setattr(OC.httpx, "get", lambda *a, **k: _Resp({"time": ["2026-09-12"]}))
    monkeypatch.setattr(OC, "_daily_cache_path", lambda lat, lon: tmp_path / "d.json")
    (p,) = OC.get_daily(1.0, 2.0)
    assert p["temp_max_c"] is None and p["condition"] is None and p["date"] == "2026-09-12"
