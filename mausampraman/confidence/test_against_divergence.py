"""Divergence dates through grade(): date, spread_mm, grade letter."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.openmeteo_client import get_divergence_scenario, prevruns_per_model
from confidence.engine import grade, model_spread

LAT, LON = 19.9975, 73.7898
DATES = ["2026-07-06", "2026-07-07", "2026-07-23", "2026-07-31", "2026-07-03"]  # golden >10mm set


def main() -> None:
    for d in DATES:
        per = prevruns_per_model(LAT, LON, d)
        scen = get_divergence_scenario(LAT, LON, d)
        spread = round(model_spread(per), 1)
        g = grade(per, None, 30, 2)
        print(f"{d}: spread_mm={spread} grade={g['grade']} scenario_precip={scen['precip_mm']}")


if __name__ == "__main__":
    main()
