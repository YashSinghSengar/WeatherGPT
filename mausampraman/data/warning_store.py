"""File-based warnings. No network, JSON per district."""
import json
from datetime import date
from pathlib import Path

DIR = Path(__file__).parent / "warnings"

ACTIVE = ("yellow", "orange", "red")
STATUS_TEXT = {
    "active_warning": "Official warning active",
    "no_warning_confirmed": "No active warning reported by the available source",
    "warning_data_unavailable": "Warning status unavailable",
    "district_not_covered": "Warning coverage unavailable for this location",
}


def _key(district: str) -> str:
    return (district or "").strip().lower()


def _synthetic(district: str, status: str) -> dict:
    today = date.today().isoformat()
    return {"district": district, "severity": "green", "headline": STATUS_TEXT[status], "body": "",
            "issued_at": today, "capture_date": today, "status": status}


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


def get_warning(district: str) -> dict:
    try:
        rec = json.loads((DIR / f"{_key(district)}.json").read_text())
    except FileNotFoundError:
        return _synthetic(district, "district_not_covered")
    except Exception:
        return _synthetic(district, "warning_data_unavailable")
    rec["status"] = "active_warning" if rec.get("severity") in ACTIVE else "no_warning_confirmed"
    return rec
