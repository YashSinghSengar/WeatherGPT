"""Calibration guard tests. Fixture errors are made-up, not real results."""
import json

from eval.calibrate import MIN_SAMPLES, calibrate, main


def _rec(i, err):
    return {"location": "Nashik", "lat": 19.99, "lon": 73.78, "forecast_time": "2026-01-01T00:00",
            "target_date": f"2026-01-{(i % 28) + 1:02d}", "horizon_days": 1, "model": "gfs_seamless",
            "predicted_precip_mm": err, "observed_precip_mm": 0.0, "absolute_error": err}


def test_no_dataset(tmp_path):
    r = calibrate([])
    assert r["status"] == "unavailable" and r["thresholds"] is None


def test_insufficient_samples(tmp_path):
    r = calibrate([_rec(0, 2.0), _rec(1, 9.0)])
    assert r["status"] == "insufficient" and r["thresholds"] is None


def test_valid_fixture_writes_separate_artifact(tmp_path):
    recs = [_rec(i, float(i % 10)) for i in range(MIN_SAMPLES + 5)]
    dest = tmp_path / "candidate.json"
    src = tmp_path / "r.jsonl"
    src.write_text("".join(json.dumps(r) + "\n" for r in recs))
    report = main(str(src), out=str(dest))
    assert report["status"] == "candidate"
    saved = json.loads(dest.read_text())
    assert set(saved["thresholds"]) == {"A_max", "B_max"}
    assert "dataset_period" in saved and saved["n_records"] == MIN_SAMPLES + 5


def test_unobserved_records_do_not_count():
    recs = [_rec(0, 2.0), {**_rec(1, 9.0), "observed_precip_mm": None, "absolute_error": None}]
    assert calibrate(recs)["status"] == "insufficient"
