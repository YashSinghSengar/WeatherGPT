# Contracts (frozen v0)

Solo project. No module owners.

## Functions

- `geocode(place: str) -> {name, lat, lon, state, country}`
- `get_forecast(lat, lon) -> {temp_c, humidity_pct, wind_kph, precip_mm, condition, source, lat, lon}`
- `get_warning(lat, lon) -> {level: none|watch|alert, headline, source}`
- `get_divergence_scenario(forecast?) -> {spread_c, scenario, source}`
- `grade(forecast, warning, divergence) -> {level: HIGH|MEDIUM|LOW, reasons[], scores}`
- `ground_check(draft, forecast, warning) -> {grounded: bool, issues[]}`
- `get_advisory(crop, forecast, warning, confidence) -> {crop, rule_id, advice_en, advice_hi, safe}`
- `phrase(advisory, forecast, warning, confidence, location, lang) -> str`
- `llm_phrase(...) -> str` same as phrase, wording only

## HTTP

- `GET /health -> {status: ok}`
- `POST /ask {query, lang: en|hi, crop} -> {answer, confidence, provenance{forecast_source, warning_source, grounded}, advisory, location, warning, forecast}`

## Principle

Deterministic code decides confidence, warnings, safety. LLM only rewords. Never invents values, never overrides warnings.
