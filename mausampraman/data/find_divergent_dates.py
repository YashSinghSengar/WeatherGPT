"""One-off: top-5 model-spread days, last 30, Nashik coords."""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.openmeteo_client import DataUnavailable, prevruns_per_model

LAT, LON = 19.9975, 73.7898
DAYS, TOP = 30, 5


def main() -> None:
    today = datetime.now(timezone.utc).date()
    rows = []
    for i in range(1, DAYS + 1):
        d = (today - timedelta(days=i)).isoformat()
        try:
            per = prevruns_per_model(LAT, LON, d)
        except DataUnavailable as e:
            print(f"{d}: unavailable ({e})")
            continue
        spread = round(max(v["rain_mm"] for v in per.values()) - min(v["rain_mm"] for v in per.values()), 1)
        detail = ", ".join(f"{m}={per[m]['rain_mm']}" for m in per)
        rows.append((spread, d))
        print(f"{d}: spread={spread} {detail}")
    rows.sort(reverse=True)
    print(f"--- top {TOP} ---")
    for spread, d in rows[:TOP]:
        print(f"{d}: spread={spread}")


if __name__ == "__main__":
    main()
