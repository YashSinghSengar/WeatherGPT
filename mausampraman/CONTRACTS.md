# Contracts (frozen v17)

Solo project. No module owners.

## Functions

- `geocode(place) -> (lat, lon) tuple | None` (None = no results; `"nashik_coastal_test"` returns Nashik stub coords without network)
- `get_forecast(lat, lon) -> {temp_c, humidity_pct?|null, wind_kph?|null, precip_mm, precip_prob_pct?|null, weather_code?|null, condition (WMO, precip fallback only if codes missing), observed_at, source, lat, lon}` (projected from canonical via to_legacy_forecast; numbers identical)
- `save_warning(district, severity, headline, body, issued_at) -> record incl. capture_date, file data/warnings/{district}.json`
- `get_warning(district) -> record incl. status: active_warning|no_warning_confirmed|warning_data_unavailable|district_not_covered` (green file = confirmed; missing = not covered; unreadable = unavailable)
- `geocode_in(place) -> (lat, lon) | None` (IN-only, no global fallback)
- `resolve_location(query, explicit?) -> (name, lat, lon) | None` (explicit wins; else IN tokens minus stopwords; else single-word global)
- `resolve_canonical(query, explicit?) -> {display_name, latitude, longitude, country?|null, state?|null, district?|null, source} | None` (same search order as resolve_location; None = unresolvable; never fabricated; raises ValueError only via canonical_location on missing coords)
- `get_canonical_weather(lat, lon) -> {location{latitude, longitude}, current{timestamp, temperature, feels_like?|null, humidity?|null, precipitation?|null, precipitation_probability?|null, wind_speed?|null, wind_direction?|null, weather_code?|null}, forecast[{timestamp, temperature?|null, precipitation?|null, precipitation_probability?|null, humidity?|null, wind_speed?|null, wind_direction?|null, weather_code?|null}], source{provider, source, retrieved_at}}` (missing stays null, never zero)
- `to_legacy_forecast(canonical) -> get_forecast shape` (pure projection, identical numbers)
- `provider.get_current/forecast/canonical/model_forecasts/daily(lat, lon[, date])` (OpenMeteoProvider; coords in, canonical out; module delegates keep the same names for callers)
- `ProviderTimeout/ProviderHTTPError/ProviderMalformed(DataUnavailable)` (structured upstream failures; existing 503/D-degrade paths unchanged)
- `plan_query(intent) -> {intent, location_required, current_weather, forecast, agreement, warnings, daily, advisory}` (deterministic; unknown intents get the unsupported plan; current+forecast share one provider fetch)
- `warning_key_for_location(canonical) -> district key` (canonical district else first token; no city cases)
- `canonical_warning(record, location?) -> {store keys, state, severity (None when unknown), description, location, source, valid_from?|null, valid_until?|null, source_reference?|null}` (state governs safety; unknown never green)
- `is_active(warning) -> bool` (status/state == active_warning only)
- `decide_advisory(crop, stage, confidence, warning_state, advisory) -> {status: advisory_available|needs_context|no_matching_rule|blocked_by_warning|insufficient_weather_data|warning_data_unavailable, missing[], advisory?|null}` (pure; never guesses; never overrides warnings)
- `grade()` override trigger is `active_warning` state (same outcomes; severity alone never overrides)
- `get_daily(lat, lon, days?=3) -> [{date, temp_max_c?|null, temp_min_c?|null, precip_mm?|null, precip_prob_pct?|null, weather_code?|null, condition?|null}]` (cached, daily API)
- `get_divergence_scenario(lat, lon, target_date?=yesterday) -> same shape as get_forecast, source openmeteo-prevruns`
- `divergence_scenario_from_models(lat, lon, per) -> same, pure no-network`
- `default_target_date() -> yesterday ISO`
- `prevruns_per_model(lat, lon, date_str) -> {model: {temp_c, rain_mm}}`
- `grade(models, warning?, feed_age_min, horizon_days) -> {grade: A|B|C|D, warning_override: bool, spread_mm, skill_prior, drivers: {spread_mm}}` (models flat or {models: {...}}; override = non-green severity -> D+True)
- `grade_forecast(forecast, warning, divergence, models?=None) -> same` (models passed by pipeline, fetched only if None)
- `ground_check(draft, forecast, warning) -> {grounded: bool, issues[]}`
- `get_advisory(crop, stage, grade) -> {crop, stage, rule_id, advice_en, advice_hi, citation, strength: strong|moderate|watch_only, safe} | None` (rules/{crop}.yaml, first stage+spread match; A/B->strong, C->moderate, D->watch_only)
- `phrase(advisory, forecast, warning, confidence, location, lang) -> str`
- `llm_phrase(...) -> str` same as phrase, wording only

## HTTP

- `GET /health -> {status: ok}`
- `POST /ask {query, lang?, language?, location?, crop?, stage?} -> {answer, intent, confidence?, provenance, advisory?, location?, warning?, forecast?, daily?}` (crop/stage opt-in, nulls on unsupported/unavailable paths; location adds optional `district`/`source`, existing `name`/`lat`/`lon`/`state`/`country` unchanged)

## Failure semantics

- geocoder/forecast upstream down -> 503 with detail, never fabricated
- divergence down -> 200, grade D + divergence-unavailable reason, spread null (never perfect agreement)
- warning store unreadable -> warning_data_unavailable record
- daily down -> daily null; LLM down -> template; per-call timeout 5s, no retries

## Principle

Deterministic code decides confidence, warnings, safety. LLM only rewords. Never invents values, never overrides warnings.
