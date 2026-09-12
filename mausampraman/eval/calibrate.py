"""Calibration guard. Derives nothing without real observations.

Report statuses:
  unavailable   - no records with observations at all
  insufficient  - some observations, fewer than MIN_SAMPLES
  candidate     - enough data; thresholds written to a SEPARATE
                  artifact for explicit review, never applied to
                  production constants here.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eval.verify_forecast import load, metrics

MIN_SAMPLES = 30  # ponytail: arbitrary floor, raise when real data arrives
DEFAULT_RECORDS = str(Path(__file__).with_name("forecast_records.jsonl"))


def calibrate(records: list) -> dict:
    obs = [r for r in records if r.get("absolute_error") is not None]
    dates = sorted({r.get("target_date") for r in obs if r.get("target_date")})
    base = {
        "dataset_period": [dates[0], dates[-1]] if dates else None,
        "locations": sorted({r.get("location") for r in obs if r.get("location")}),
        "n_records": len(obs),
        "horizons": sorted({r.get("horizon_days") for r in obs if r.get("horizon_days") is not None}),
        "model_coverage": sorted({r.get("model") for r in obs if r.get("model")}),
        "error_metric": "mean_absolute_error_precip_mm",
        "threshold_method": None,
        "thresholds": None,
    }
    if not obs:
        return {**base, "status": "unavailable", "reason": "no records with observations"}
    if len(obs) < MIN_SAMPLES:
        return {**base, "status": "insufficient", "reason": f"{len(obs)} < {MIN_SAMPLES} minimum samples"}
    errs = sorted(r["absolute_error"] for r in obs)
    q = lambda p: errs[min(int(p * len(errs)), len(errs) - 1)]
    return {**base, "status": "candidate", "reason": "review required before use",
            "threshold_method": "empirical tertiles of absolute error (candidate only, not production)",
            "thresholds": {"A_max": q(1 / 3), "B_max": q(2 / 3)}}


def main(path: str = DEFAULT_RECORDS, out: str | None = None) -> dict:
    report = calibrate(load(path))
    if report["status"] == "candidate":
        dest = out or str(Path(path).with_name("calibration_candidate.json"))
        Path(dest).write_text(json.dumps(report, indent=2))
        report["artifact"] = dest
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RECORDS)
