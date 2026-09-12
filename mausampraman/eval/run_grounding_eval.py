"""Grounding eval: precision/recall/false accepts/rejects. No LLM evaluator."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from confidence.grounding import ground_check


def _cat(issue: str) -> str:
    return issue.split(":")[0]


def main(path: str | None = None) -> dict:
    path = path or str(Path(__file__).with_name("grounding_questions.json"))
    items = json.loads(Path(path).read_text())
    tp = fp = tn = fn = 0
    fails = []
    for it in items:
        r = ground_check(it["draft"], it["forecast"], it["warning"], it.get("confidence"), it.get("advisory"), it.get("location"))
        exp = it["expected_grounded"]
        if r["grounded"] and exp:
            tp += 1
        elif r["grounded"] and not exp:
            fp += 1
        elif not r["grounded"] and not exp:
            tn += 1
        else:
            fn += 1
        got_cats = {_cat(i) for i in r["issues"]}
        missing = [e for e in it.get("expected_issues", []) if _cat(e) not in got_cats]
        if (r["grounded"] != exp) or missing:
            fails.append({"id": it.get("id"), "expected_grounded": exp, "got_grounded": r["grounded"],
                          "issues": r["issues"], "missing_expected": missing})
    report = {"n": len(items),
              "precision": round(tp / (tp + fp), 3) if tp + fp else None,
              "recall": round(tp / (tp + fn), 3) if tp + fn else None,
              "false_accepts": fp, "false_rejects": fn,
              "corrupted_caught": tn, "corrupted_total": tn + fp,
              "failures": fails}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
