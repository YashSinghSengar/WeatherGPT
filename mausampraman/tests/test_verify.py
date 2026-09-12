"""Fixture values below are made-up test data, NOT real-world results."""
from eval.verify_forecast import OBSERVATION_INGESTION_AVAILABLE, append_forecast, append_observation, load, metrics

FIXTURES = [
    ("Nashik", 19.99, 73.78, "2026-09-01T00:00", "2026-09-02", 1, "gfs_seamless", 2.0, 5.0),
    ("Nashik", 19.99, 73.78, "2026-09-01T00:00", "2026-09-02", 1, "ecmwf_ifs025", 8.0, 5.0),
    ("Pune", 18.52, 73.85, "2026-09-01T00:00", "2026-09-03", 2, "gfs_seamless", 0.0, 1.0),
]


def _seed(path):
    for loc, lat, lon, ft, td, h, m, pred, obs in FIXTURES:
        append_forecast(path, location=loc, lat=lat, lon=lon, forecast_time=ft, target_date=td, horizon_days=h, model=m, predicted_precip_mm=pred)
        append_observation(path, location=loc, target_date=td, model=m, observed_precip_mm=obs)


def test_append_and_observe(tmp_path):
    p = tmp_path / "r.jsonl"
    _seed(p)
    recs = load(p)
    assert len(recs) == 3 and all(r["absolute_error"] is not None for r in recs)
    assert recs[0]["absolute_error"] == 3.0


def test_metrics_math(tmp_path):
    p = tmp_path / "r.jsonl"
    _seed(p)
    m = metrics(load(p))
    assert m["samples"] == {"n": 3, "mae": round((3.0 + 3.0 + 1.0) / 3, 2)}
    assert m["by_model"]["gfs_seamless"] == {"n": 2, "mae": 2.0}
    assert m["by_model"]["ecmwf_ifs025"] == {"n": 1, "mae": 3.0}
    assert m["by_horizon"][1] == {"n": 2, "mae": 3.0}
    assert m["by_location"]["Pune"] == {"n": 1, "mae": 1.0}


def test_observation_ingestion_flagged_unavailable():
    assert OBSERVATION_INGESTION_AVAILABLE is False


def test_missing_file_and_no_match(tmp_path):
    p = tmp_path / "empty.jsonl"
    assert load(p) == []
    assert metrics([])["samples"] == {"n": 0, "mae": None}
    assert append_observation(p, location="X", target_date="d", model="m", observed_precip_mm=1.0) == 0
