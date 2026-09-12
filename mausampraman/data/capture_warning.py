"""Capture a district warning: python data/capture_warning.py Nashik orange "headline" "body text"."""
import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.warning_store import save_warning


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("district")
    ap.add_argument("severity", choices=["green", "yellow", "orange", "red"])
    ap.add_argument("headline")
    ap.add_argument("body")
    a = ap.parse_args()
    rec = save_warning(a.district, a.severity, a.headline, a.body, date.today().isoformat())
    print(f"saved data/warnings/{a.district.strip().lower()}.json capture_date={rec['capture_date']}")


if __name__ == "__main__":
    main()
