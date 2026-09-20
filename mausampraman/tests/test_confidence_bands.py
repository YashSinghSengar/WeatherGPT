import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from confidence.engine import grade
# Tight agreement, fresh data, short horizon -> A
assert grade({"models":{"a":{"rain_mm":3},"b":{"rain_mm":4},"c":{"rain_mm":3.5}}}, None, 30, 1)["grade"] == "A"
# Wide spread -> C or D
assert grade({"models":{"a":{"rain_mm":2},"b":{"rain_mm":28},"c":{"rain_mm":9}}}, None, 30, 2)["grade"] in ("C","D")
# Warning overrides everything regardless of spread (state governs, not severity alone)
assert grade({"models":{"a":{"rain_mm":3}}}, {"severity":"orange","status":"active_warning"}, 10, 1)["grade"] == "D"
assert grade({"models":{"a":{"rain_mm":3}}}, {"severity":"orange","status":"active_warning"}, 10, 1)["warning_override"] == True
# Unknown coverage never overrides, even with a stale severity label
assert grade({"models":{"a":{"rain_mm":3}}}, {"severity":"green","status":"warning_data_unavailable"}, 10, 1)["grade"] == "A"
print("all confidence engine tests passed")
