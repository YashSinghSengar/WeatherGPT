"""Intent eval: accuracy, per-intent, confusion, failures. No LLM scoring."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.intent import classify_intent


def main(path: str | None = None) -> dict:
    path = path or str(Path(__file__).with_name("intent_questions.json"))
    items = json.loads(Path(path).read_text())
    per, conf, fails = defaultdict(lambda: [0, 0]), Counter(), []
    for it in items:
        got = classify_intent(it["q"])["intent"]
        exp = it["expected"]
        per[exp][0] += (got == exp)
        per[exp][1] += 1
        conf[(exp, got)] += 1
        if got != exp:
            fails.append({"q": it["q"], "expected": exp, "got": got})
    n = len(items)
    report = {"n": n, "accuracy": round((n - len(fails)) / n, 3) if n else None,
              "per_intent": {k: {"n": t, "accuracy": round(a / t, 3)} for k, (a, t) in sorted(per.items())},
              "confusion": {f"{e}->{g}": c for (e, g), c in sorted(conf.items()) if e != g},
              "failures": fails,
              "note": "project evaluation set, not a real user population"}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
