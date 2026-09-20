"""Integrated MausamPraman evaluation. Deterministic fixtures, no network.

Covers: location, intent, weather integrity, warnings, agreement,
grounding, advisory safety, EN/HI phrasing, unsupported queries,
failure handling, LLM fallback. Metrics never manufactured:
unavailable reads "not evaluated".
"""
import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

LIMITATIONS = [
    "live upstream APIs are mocked here; see tests/live for smoke coverage",
    "Hindi prose quality is human-review only, never auto-scored",
    "calibration dataset absent: agreement grades are not probabilities",
    "warning store covers captured districts only, not official global state",
    "no browser automation: frontend click paths verified by build + served HTML",
]


def _quiet(fn, *a):
    with redirect_stdout(io.StringIO()):
        return fn(*a)


def main() -> dict:
    from eval.run_intent_eval import main as intent_eval
    from eval.run_grounding_eval import main as grounding_eval
    from eval.run_agreement_eval import main as agreement_eval
    from eval.run_phrasing_eval import main as phrasing_eval
    from eval.run_warning_eval import main as warning_eval
    from eval.run_advisory_eval import main as advisory_eval
    from eval.run_integration_eval import main as integration_eval
    from data.warning_store import get_warning

    intent = _quiet(intent_eval)
    grounding = _quiet(grounding_eval)
    agreement = _quiet(agreement_eval)
    phrasing = _quiet(phrasing_eval)
    warnings = _quiet(warning_eval)
    advisory = _quiet(advisory_eval)
    integration = _quiet(integration_eval)

    warn = get_warning("nashik_coastal_test")
    overrides = agreement.get("warning_override", [])
    warning_safety = {"fixture_orange_preserved": warn["status"] == "active_warning",
                      "override_always_D": all(o["grade"] == "D" for o in overrides) if overrides else "not evaluated"}
    unsupported = {"intent": intent["per_intent"].get("unsupported", {}).get("accuracy")}
    failures = {"resilience_suite": "see pytest", "llm_fallback_kept": phrasing["kept_correct"] == phrasing["n"]}
    try:
        pt = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:warnings"],
                            capture_output=True, text=True, cwd=str(Path(__file__).resolve().parents[1]),
                            timeout=600)
        tail = pt.stdout.strip().splitlines()[-1] if pt.stdout.strip() else ""
    except Exception as e:
        tail = f"pytest not run: {e}"
    report = {"tests": tail,
              "intent_accuracy": intent["accuracy"],
              "grounding": {"precision": grounding["precision"], "recall": grounding["recall"],
                            "false_accepts": grounding["false_accepts"], "false_rejects": grounding["false_rejects"]},
              "agreement": {"distribution": agreement["grade_distribution"], "failures": agreement["failures"]},
              "warnings": {"passed": warnings["passed"], "n": warnings["n"], "failures": warnings["failures"]},
              "advisory": {"passed": advisory["passed"], "n": advisory["n"], "failures": advisory["failures"]},
              "integration": {"passed": integration["passed"], "n": integration["n"], "failures": integration["failures"]},
              "warning_safety": warning_safety,
              "unsupported_query_accuracy": unsupported["intent"],
              "failure_handling": failures,
              "known_limitations": LIMITATIONS}
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
