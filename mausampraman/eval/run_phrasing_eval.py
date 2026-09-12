"""Phrasing eval: safety checks on mocked LLM outputs. Hindi quality = human review only."""
import json
import re
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from phrasing.llm_phrase import phrase
from phrasing.templates import render_template


class _Resp:
    def __init__(self, mode, text=""):
        self.mode, self.text = mode, text
    def raise_for_status(self):
        if self.mode == "MALFORMED":
            raise ValueError("bad status")
    def json(self):
        if self.mode == "MALFORMED":
            return {"nope": []}
        return {"choices": [{"message": {"content": self.text}}]}


def _nums(text):
    return [float(m) for m in re.findall(r"[+-]?\d+(?:\.\d+)?", str(text or ""))]


def checks(item, out, fallback):
    p = item["payload"]
    vals = [float(v) for v in (p.get("values") or {}).values() if isinstance(v, (int, float))]
    letters = set(re.findall(r"\b[A-D]\b", out))
    return {
        "no_invented_numbers": all(any(o == a for a in vals) for o in _nums(out)),
        "warning_preserved": (not p.get("warning_text")) or (p["warning_text"] in out),
        "grade_preserved": (not letters) or letters == {(p.get("grade") or "")},
        "action_preserved": all(w.lower() in out.lower() for w in re.findall(r"[A-Za-z]+", str(p.get("action") or "")) if len(w) > 3) if item["lang"] == "en" else "manual-review",
        "length_ok": len(out) <= 400,
        "fallback_used": out == fallback,
        "no_exception": True,
    }


def main(path=None):
    path = path or str(Path(__file__).with_name("phrasing_questions.json"))
    items = json.loads(Path(path).read_text())
    results, review = [], []
    orig = httpx.post
    import os
    saved_key = os.environ.get("SARVAM_API_KEY")
    os.environ["SARVAM_API_KEY"] = "eval-fake-key"
    try:
        for it in items:
            mode = it["mock"]
            try:
                if mode == "TIMEOUT":
                    def boom(*a, **k):
                        raise httpx.TimeoutException("slow")
                    httpx.post = boom
                else:
                    def fake_post(*a, _m=mode, **k):
                        return _Resp(_m, _m if _m != "MALFORMED" else "")
                    httpx.post = fake_post
                out = phrase(it["payload"], it["lang"])
            except Exception as e:
                out = f"EXCEPTION:{e}"
            finally:
                httpx.post = orig
            fallback = render_template(it["payload"], it["lang"])
            kept = out != fallback
            ck = checks(it, out, fallback) if not out.startswith("EXCEPTION") else {"no_exception": False}
            results.append({"id": it["id"], "kept_mock": kept, "expected_kept": it["expect_kept"], "checks": ck,
                            "output": out[:200]})
            if kept != it["expect_kept"] or not all(v is True for v in ck.values()):
                review.append({"id": it["id"], "output": out[:300]})
    finally:
        if saved_key is None:
            os.environ.pop("SARVAM_API_KEY", None)
        else:
            os.environ["SARVAM_API_KEY"] = saved_key
    report = {"n": len(items),
              "kept_correct": sum(1 for r in results if r["kept_mock"] == r["expected_kept"]),
              "all_checks_pass": all(all(v is True or v == "manual-review" or k == "fallback_used" for k, v in r["checks"].items()) for r in results),
              "results": results,
              "manual_review_Hindi_quality_only": [r for r in results if r["id"].startswith("p-hi")] + review}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
