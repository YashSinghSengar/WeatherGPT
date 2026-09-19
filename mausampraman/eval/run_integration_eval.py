"""Integration eval: 10 mocked end-to-end cases. No network, no LLM calls."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import api.main as M
from fastapi.testclient import TestClient
from tests.fixtures import PER_NORMAL, forecast, warning_green, warning_orange, warning_unavailable

c = TestClient(M.app)
NAMES = ("resolve_canonical", "get_forecast", "get_warning", "prevruns_per_model", "get_daily")
SAVED = {n: getattr(M, n) for n in NAMES}


def _wire(resolve=None, warning="green", divergent=False):
    from tests.fixtures import resolve_canonical_fake
    w = {"green": warning_green(), "orange": warning_orange(), "unavailable": warning_unavailable()}[warning]
    M.resolve_canonical = resolve_canonical_fake("*") if resolve is None else resolve
    M.get_forecast = lambda lat, lon: {**forecast("Nashik"), "lat": lat, "lon": lon}
    M.get_warning = lambda d: w
    M.prev_runs_calls = 0
    def prevruns(lat, lon, day):
        M.prev_runs_calls += 1
        from tests.fixtures import PER_DIVERGENT
        return PER_DIVERGENT if divergent else PER_NORMAL
    M.prevruns_per_model = prevruns
    M.get_daily = lambda lat, lon: []


def _restore():
    for n in NAMES:
        setattr(M, n, SAVED[n])


def main() -> dict:
    results = []

    def case(cid, body, check, **wire):
        _wire(**wire)
        try:
            r = c.post("/ask", json=body)
            d = r.json()
            ok, detail = check(r.status_code, d)
            results.append({"id": cid, "ok": bool(ok), "detail": detail})
        finally:
            _restore()

    case("current", {"query": "What is the temperature in Delhi?", "language": "en"},
         lambda s, d: (s == 200 and d["location"]["name"] == "Delhi" and d["advisory"] is None
                       and d["evidence"]["weather"]["values"]["temperature"] == 25.0, "weather+evidence"))
    case("rain", {"query": "Will it rain tonight in Nashik?", "language": "en"},
         lambda s, d: (s == 200 and "3.0mm" in d["answer"] and d["confidence"]["spread_mm"] == 2.0
                       and M.prev_runs_calls == 1, "shared model data"))
    case("warning", {"query": "Is there a warning for Pune?", "language": "en"},
         lambda s, d: (s == 200 and d["forecast"] is None and d["advisory"] is None
                       and d["warning"]["state"] == "district_not_covered", "warning-only"))
    case("agri", {"query": "Should I irrigate grapes in Nashik?", "crop": "grape",
                  "stage": "veraison", "language": "en"},
         lambda s, d: (s == 200 and d["advisory"] is not None and d["evidence"]["advisory"]["rule_id"]
                       == d["advisory"]["rule_id"], "advisory+provenance"))
    case("confidence", {"query": "Why is the Nashik forecast B?", "language": "en"},
         lambda s, d: (s == 200 and d["forecast"] is None and "agreement" in d["answer"].lower()
                       and d["confidence"]["grade"] in ("A", "B", "C", "D"), "agreement-only"))
    case("unsupported", {"query": "Tell me a joke", "language": "en"},
         lambda s, d: (s == 200 and d["forecast"] is None and d["warning"] is None, "skipped"),
         resolve=lambda q, loc=None: None)
    case("orange-agri", {"query": "Should I irrigate grapes in Nashik?", "crop": "grape",
                         "stage": "veraison", "language": "en"},
         lambda s, d: (s == 200 and d["advisory"] is None and "warning" in d["answer"].lower()
                       and d["confidence"]["warning_override"] is True, "blocked"),
         warning="orange")
    case("warning-unavailable", {"query": "Is there a warning for Pune?", "language": "en"},
         lambda s, d: (s == 200 and d["warning"]["state"] == "warning_data_unavailable"
                       and "no warning" not in d["answer"].lower(), "uncertainty-kept"),
         warning="unavailable")
    case("new-location", {"query": "Will it rain in Gwalior?", "language": "en"},
         lambda s, d: (s == 200 and d["location"]["name"] == "Gwalior"
                       and d["forecast"] is not None, "arbitrary-place"))
    from phrasing.llm_phrase import phrase as llm_phrase
    import httpx
    real_post, real_key = httpx.post, os.environ.get("SARVAM_API_KEY")
    os.environ["SARVAM_API_KEY"] = "x"
    httpx.post = lambda *a, **k: 1 / 0
    try:
        out = llm_phrase({"grade": "B", "action": "Act.", "rationale": "Why.", "values": {}}, "en")
        results.append({"id": "sarvam-fallback", "ok": out.startswith("Grade B"), "detail": "template"})
    finally:
        httpx.post = real_post
        if real_key is None:
            os.environ.pop("SARVAM_API_KEY", None)
        else:
            os.environ["SARVAM_API_KEY"] = real_key

    fails = [r for r in results if not r["ok"]]
    report = {"n": len(results), "passed": len(results) - len(fails), "failures": fails}
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
