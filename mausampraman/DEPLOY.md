# Deploy (Render + static frontend)

No secrets in this file. Set real values in dashboards, never commit them.

## Backend (Render web service, see render.yaml)

- Start: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- Health check: `GET /health` (no auth, returns `{"status":"ok"}`)
- Required env:
  - `FRONTEND_ORIGIN` — exact prod frontend origin, e.g.
    `https://mausampraman.vercel.app`. When set, it is the
    ONLY allowed CORS origin. When unset, local dev origins
    (`localhost:3000/3001`, `127.0.0.1:3000/3001`) apply.
  - `SARVAM_API_KEY` — Sarvam key for LLM wording only.
    Absent key = deterministic template fallback, never an error.

## Frontend (any static host)

- Build with `NEXT_PUBLIC_API_URL` set to the backend URL,
  e.g. `https://mausampraman-api.onrender.com`. Next.js bakes
  this in at build time; localhost fallback applies only when unset.
- No secret lives in the frontend bundle.

## Local dev

Backend `:8000`, frontend `:3000`. No env needed except
`SARVAM_API_KEY` in `mausampraman/.env` for live LLM wording.
