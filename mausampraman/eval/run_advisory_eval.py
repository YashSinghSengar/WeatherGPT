"""Advisory eval: opt-in, context, safety. Deterministic rule selection only."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from advisory.engine import decide_advisory, get_advisory

CONF = {"grade": "B", "warning_override": False, "spread_mm": 6.0,
        "skill_prior": 0.0, "drivers": {"spread_mm": 6.0}}
ADV = {"rule_id": "r1"}


def main() -> dict:
    real = get_advisory("grape", "veraison", {**CONF, "drivers": {"spread_mm": 2.0}})
    cases = [
        ("valid", decide_advisory("grape", "veraison", CONF, "no_warning_confirmed", ADV)["status"], "advisory_available"),
        ("missing-crop", decide_advisory(None, "veraison", CONF, "no_warning_confirmed", None)["status"], "needs_context"),
        ("missing-stage", decide_advisory("grape", None, CONF, "no_warning_confirmed", None)["status"], "needs_context"),
        ("no-rule", decide_advisory("grape", "veraison", CONF, "no_warning_confirmed", None)["status"], "no_matching_rule"),
        ("blocked", decide_advisory("grape", "veraison", CONF, "active_warning", ADV)["status"], "blocked_by_warning"),
        ("unavailable", decide_advisory("grape", "veraison", CONF, "warning_data_unavailable", ADV)["status"], "warning_data_unavailable"),
        ("not-covered", decide_advisory("grape", "veraison", CONF, "district_not_covered", ADV)["status"], "advisory_available"),
        ("no-weather", decide_advisory("grape", "veraison", None, "no_warning_confirmed", None)["status"], "insufficient_weather_data"),
        ("rule-select", (real or {}).get("rule_id") is not None and real.get("strength") in ("strong", "moderate", "watch_only"), True),
    ]
    fails = [{"id": cid, "got": got, "expected": exp} for cid, got, exp in cases if got != exp]
    report = {"n": len(cases), "passed": len(cases) - len(fails), "failures": fails,
              "note": "advice quality never auto-scored, only selection and safety"}
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
