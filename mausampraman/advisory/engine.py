"""Deterministic advisory. Parses rules YAML, no LLM, no eval()."""
import pathlib

STRENGTH = {"A": "strong", "B": "strong", "C": "moderate"}  # else watch_only


def _holds(cond: str, value: float) -> bool:
    c = (cond or "").strip()
    for op in ("<=", ">=", "==", "<", ">"):
        if c.startswith(op):
            try:
                num = float(c[len(op):].strip())
            except ValueError:
                return False
            return {"<=": value <= num, ">=": value >= num, "==": value == num, "<": value < num, ">": value > num}[op]
    return False


def _load_rules(crop: str) -> list:
    p = pathlib.Path(__file__).parent / "rules" / f"{crop}.yaml"
    if not p.exists():
        return []
    rules, cur = [], None
    for raw in p.read_text().splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if not raw.startswith((" ", "\t")):
            cur = None  # top-level key (crop/version/rules:), not a rule field
            continue
        if s.startswith("- "):
            cur = {}
            rules.append(cur)
            s = s[2:].strip()
            if not s:
                continue
        if cur is None or ":" not in s:
            continue
        k, v = s.split(":", 1)
        cur[k.strip()] = v.strip().strip("\"'")
    return rules


def get_advisory(crop: str, stage: str, grade: dict) -> dict | None:
    spread = (grade.get("drivers") or {}).get("spread_mm")
    if spread is None:
        return None
    strength = STRENGTH.get(grade.get("grade"), "watch_only")
    for r in _load_rules(crop):
        if r.get("stage") != stage or not _holds(r.get("when", ""), spread):
            continue
        return {
            "crop": crop,
            "stage": stage,
            "rule_id": r.get("id"),
            "advice_en": r.get("advice_en", ""),
            "advice_hi": r.get("advice_hi", ""),
            "citation": r.get("citation", ""),
            "strength": strength,
            "safe": strength in ("strong", "moderate"),
        }
    return None
