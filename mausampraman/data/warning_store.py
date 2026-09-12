"""File-based warnings. No network, JSON per district."""
import json
from datetime import date
from pathlib import Path

DIR = Path(__file__).parent / "warnings"


def _key(district: str) -> str:
    return (district or "").strip().lower()


def save_warning(district: str, severity: str, headline: str, body: str, issued_at: str) -> dict:
    record = {
        "district": district,
        "severity": severity,
        "headline": headline,
        "body": body,
        "issued_at": issued_at,
        "capture_date": date.today().isoformat(),
    }
    DIR.mkdir(parents=True, exist_ok=True)
    (DIR / f"{_key(district)}.json").write_text(json.dumps(record, indent=2))
    return record


def get_warning(district: str) -> dict | None:
    try:
        return json.loads((DIR / f"{_key(district)}.json").read_text())
    except Exception:
        return None
