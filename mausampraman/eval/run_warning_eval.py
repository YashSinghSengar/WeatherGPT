"""Warning eval: states, severities, safety. No network, temp store dir."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import data.warning_store as WS
from confidence.engine import grade
from data.warnings import canonical_warning, is_active

PER = {"gfs_seamless": {"temp_c": 25.0, "rain_mm": 2.0},
       "ecmwf_ifs025": {"temp_c": 26.0, "rain_mm": 4.0},
       "icon_seamless": {"temp_c": 25.5, "rain_mm": 3.0}}


def main() -> dict:
    tmp = tempfile.mkdtemp()
    real_dir = WS.DIR
    WS.DIR = Path(tmp)
    checks = []
    try:
        WS.save_warning("Active", "orange", "Heavy rain", "Stay in.", "2026-01-01")
        WS.save_warning("Calm", "green", "Calm", "", "2026-01-01")
        WS.save_warning("Yellow", "yellow", "Watch", "", "2026-01-01")
        WS.save_warning("Red", "red", "Extreme", "Leave.", "2026-01-01")
        cases = [
            ("active-orange", WS.get_warning("Active"), "active_warning", "orange", True),
            ("confirmed-calm", WS.get_warning("Calm"), "no_warning_confirmed", "green", False),
            ("active-yellow", WS.get_warning("Yellow"), "active_warning", "yellow", True),
            ("active-red", WS.get_warning("Red"), "active_warning", "red", True),
            ("not-covered", WS.get_warning("Nowhere"), "district_not_covered", None, False),
        ]
        for cid, rec, exp_state, exp_sev, exp_active in cases:
            w = canonical_warning(rec)
            ok = w["state"] == exp_state and w["severity"] == exp_sev and is_active(w) == exp_active
            checks.append({"id": cid, "ok": ok, "state": w["state"], "severity": w["severity"]})
        g = grade(PER, WS.get_warning("Active"), 0.0, 2)
        checks.append({"id": "override-active", "ok": g["grade"] == "D" and g["warning_override"] is True})
        g2 = grade(PER, WS.get_warning("Calm"), 0.0, 2)
        checks.append({"id": "no-override-calm", "ok": g2["warning_override"] is False})
        g3 = grade(PER, WS.get_warning("Nowhere"), 0.0, 2)
        checks.append({"id": "no-override-uncovered", "ok": g3["warning_override"] is False})
    finally:
        WS.DIR = real_dir
    fails = [c for c in checks if not c["ok"]]
    report = {"n": len(checks), "passed": len(checks) - len(fails), "failures": fails,
              "note": "missing warning data never becomes no warning"}
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
