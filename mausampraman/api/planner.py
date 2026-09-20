"""Deterministic query planner. Intent in, capability flags out.

No LLM decides execution. Current + forecast views share one provider
fetch; agreement needs per-model data; warnings/advisory are gated.
Agreement and warnings stay on for every located intent because the
frozen answer shape carries grade and warning state.
"""

PLANS = {
    "weather_current": {"location_required": True, "current_weather": True, "forecast": True,
                        "agreement": True, "warnings": True, "daily": True, "advisory": False},
    "forecast_rain": {"location_required": True, "current_weather": False, "forecast": True,
                      "agreement": True, "warnings": True, "daily": True, "advisory": False},
    "warning_status": {"location_required": True, "current_weather": False, "forecast": False,
                       "agreement": True, "warnings": True, "daily": False, "advisory": False},
    "agriculture_advice": {"location_required": True, "current_weather": False, "forecast": True,
                           "agreement": True, "warnings": True, "daily": True, "advisory": True},
    "confidence_explanation": {"location_required": True, "current_weather": False, "forecast": False,
                               "agreement": True, "warnings": True, "daily": False, "advisory": False},
    "unsupported": {"location_required": False, "current_weather": False, "forecast": False,
                    "agreement": False, "warnings": False, "daily": False, "advisory": False},
}


def plan_query(intent_name: str) -> dict:
    """Capability flags for one intent. Unknown intents get the unsupported plan."""
    plan = PLANS.get(intent_name, PLANS["unsupported"])
    return {"intent": intent_name, **plan}
