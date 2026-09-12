"""Agreement eval: grade distribution, failures, override/missing-data behavior."""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from confidence.engine import grade

TERMS = {"forecast agreement", "model agreement", "agreement"}


def main(path: str | None = None) -> dict:
    path = path or str(Path(__file__).with_name("agreement_questions.json"))
    items = json.loads(Path(path).read_text())
    dist, fails, overrides, missing = Counter(), [], [], []
    for it in items:
        if "recorded" in it:
            r = it["recorded"]
            models = {k: {"rain_mm": v} for k, v in (("gfs", r["gfs"]), ("ecmwf", r["ecmwf"]), ("icon", r["icon"]))}
        else:
            models = it["models"]
        try:
            got = grade(models, it["warning"], it["feed_age_min"], it["horizon_days"])["grade"]
        except Exception as e:
            got = f"error:{type(e).__name__}"
        dist[got] += 1
        if it["warning"]:
            overrides.append({"id": it.get("id"), "grade": got})
        if not models or any(v.get("rain_mm") is None for v in models.values()):
            missing.append({"id": it.get("id"), "grade": got})
        exp = it["expected_grade"]
        ok = got == exp or (exp == "error" and got.startswith("error"))
        if not ok:
            fails.append({"id": it.get("id"), "expected": exp, "got": got})
    report = {"n": len(items), "grade_distribution": dict(sorted(dist.items())), "failures": fails,
              "warning_override": overrides, "missing_data": missing,
              "terminology": "forecast agreement (no calibration claimed)"}
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
