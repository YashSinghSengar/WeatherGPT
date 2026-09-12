# Contracts (frozen v8)

Solo project. No module owners.

## Functions

- `geocode(place) -> (lat, lon) tuple | None` (None = no results; `"nashik_coastal_test"` returns Nashik stub coords without network)
- `get_forecast(lat, lon) -> {temp_c, humidity_pct, wind_kph, precip_mm, condition, source, lat, lon}`
- `save_warning(district, severity, headline, body, issued_at) -> record incl. capture_date, file data/warnings/{district}.json`
- `get_warning(district) -> record incl. capture_date | None` (severity green|yellow|orange|red; only green = no-warning)
- `geocode_in(place) -> (lat, lon) | None` (IN-only, no global fallback)
- `resolve_location(query, explicit?) -> (name, lat, lon) | None` (explicit wins; else IN tokens minus stopwords; else single-word global)
- `get_divergence_scenario(lat, lon, target_date?=yesterday) -> same shape as get_forecast, source openmeteo-prevruns`
- `prevruns_per_model(lat, lon, date_str) -> {model: {temp_c, rain_mm}}`
- `grade(models, warning?, feed_age_min, horizon_days) -> {grade: A|B|C|D, warning_override: bool, spread_mm, skill_prior, drivers: {spread_mm}}` (models flat or {models: {...}}; override = non-green severity -> D+True)
- `grade_forecast(forecast, warning, divergence) -> same` (derives models/age/horizon, pipeline adapter)
- `ground_check(draft, forecast, warning) -> {grounded: bool, issues[]}`
- `get_advisory(crop, stage, grade) -> {crop, stage, rule_id, advice_en, advice_hi, citation, strength: strong|moderate|watch_only, safe} | None` (rules/{crop}.yaml, first stage+spread match; A/B->strong, C->moderate, D->watch_only)
- `phrase(advisory, forecast, warning, confidence, location, lang) -> str`
- `llm_phrase(...) -> str` same as phrase, wording only

## HTTP

- `GET /health -> {status: ok}`
- `POST /ask {query, lang?, language?, location?, crop, stage} -> {answer, intent, confidence?, provenance, advisory?, location?, warning?, forecast?}` (nulls on unsupported/unavailable paths)

## Principle

Deterministic code decides confidence, warnings, safety. LLM only rewords. Never invents values, never overrides warnings.
