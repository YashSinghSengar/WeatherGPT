# MausamPraman (scaffold v0)

Trustworthy weather intelligence, India. Deterministic confidence first, LLM wording only.

## Run backend
```
cd mausampraman
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```
Check: `curl localhost:8000/health`, `curl -X POST localhost:8000/ask -H 'Content-Type: application/json' -d '{"query":"Nashik","lang":"en"}'`

## Run frontend
```
cd mausampraman/web
npm install
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000 npm run dev
```
Open http://localhost:3000

## Tests
```
cd mausampraman
pytest -q
```
