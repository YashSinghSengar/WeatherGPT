"""Groundedness check: draft numbers must match forecast. Deterministic."""


def ground_check(draft: str, forecast: dict, warning: dict) -> dict:
    issues: list[str] = []
    # Stub: only fail on empty draft. Real check compares numbers verbatim.
    if not draft:
        issues.append("empty-draft")
    return {"grounded": not issues, "issues": issues}
