"""Warning boundary. Store record in, canonical warning out.

State is authoritative. Severity is only meaningful for active or
confirmed-calm warnings; unknown coverage never poses as green.
File store stays; no database.
"""

from data.warning_store import ACTIVE

ACTIVE_STATES = ("active_warning",)
UNKNOWN_STATES = ("warning_data_unavailable", "district_not_covered")


def warning_key_for_location(location: dict | None) -> str:
    """District key from canonical location. No city special-cases."""
    location = location or {}
    district = location.get("district") or (location.get("display_name") or location.get("name") or "")
    return str(district).split()[0].lower() if str(district).split() else ""


def canonical_warning(record: dict, location: dict | None = None) -> dict:
    """Full warning shape. Store keys kept; state governs safety, never severity."""
    record = record or {}
    status = record.get("status")
    if status is None:  # ponytail: legacy-shaped dicts only; store always stamps status
        status = "active_warning" if record.get("severity") in ACTIVE else "no_warning_confirmed"
    severity = record.get("severity")
    if status in UNKNOWN_STATES:
        severity = None
    out = dict(record)
    out.update({
        "state": status,
        "severity": severity,
        "description": record.get("description", record.get("body", "")),
        "location": {"district": record.get("district")},
        "source": record.get("source", "warnings-store"),
        "valid_from": record.get("valid_from"),
        "valid_until": record.get("valid_until"),
        "source_reference": record.get("source_reference"),
    })
    if location is not None:
        out["location"] = {"district": record.get("district"),
                           "latitude": location.get("lat"), "longitude": location.get("lon")}
    return out


def is_active(warning: dict) -> bool:
    """Single deterministic safety signal. Unknown never counts as safe-or-active."""
    w = warning or {}
    return w.get("status") == "active_warning" or w.get("state") == "active_warning"
