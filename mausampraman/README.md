# MausamPraman

Trustworthy weather intelligence, India. Deterministic agreement + grounding first, LLM wording only.

## Run backend
```
cd mausampraman
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```
Check: `curl localhost:8000/health`, `curl -X POST localhost:8000/ask -H 'Content-Type: application/json' -d '{"query":"Nashik","language":"en"}'`

## Run frontend
```
cd mausampraman/web
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```
Open http://localhost:3000

## Tests and evaluation
```
cd mausampraman
pytest -q                        # offline unit suite (live smoke in tests/live/)
MAUSAM_OFFLINE=1 pytest -q       # prove no network needed
python3 eval/run_all.py          # integrated evaluation report
python3 eval/run_golden_set.py   # live golden questions (needs backend)
```

## Status (honest)

IMPLEMENTED: intent routing (6 intents), location resolution with IN
preference, Open-Meteo forecast + daily + 3-model divergence, file
warning store with 4 explicit states, A-D agreement bands, YAML grape
advisory (opt-in), deterministic grounding validator, Sarvam phrasing
with validation + template fallback, failure semantics (503/D-degrade),
request ids + JSON logs, offline test suite, 5 deterministic eval suites.

PARTIALLY IMPLEMENTED: LLM wording (works when key + fast model answer
in budget, else template); Hindi (pipeline + templates real, prose
quality human-review only); calibration (machinery + guard exist, zero
real observations, grades are agreement not probability).

DEFERRED: real NER for locations, IMD warning feed, more crops, browser
geolocation, hourly timeline UI, production deployment. Not production
ready; prototype with measured claims only.
