# ⛅ MausamPraman (मौसम प्रमाण)
### *Trustworthy Weather Intelligence for India — Deterministic Grounding First, LLM Wording Only*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![Data Source](https://img.shields.io/badge/Data-Open--Meteo-orange.svg)](https://open-meteo.com/)
[![LLM Phrasing](https://img.shields.io/badge/LLM-Sarvam%20AI-purple.svg)](https://www.sarvam.ai/)
[![Status](https://img.shields.io/badge/Status-Prototype%20%2F%20Measured-green.svg)](#-status--roadmap)

---

## 📌 Table of Contents
- [📖 Overview](#-overview)
- [🎯 Key Highlights & Principles](#-key-highlights--principles)
- [🧱 System Architecture & Data Flow](#-system-architecture--data-flow)
- [📊 Agreement Bands & Confidence Matrix](#-agreement-bands--confidence-matrix)
- [🚀 Quick Start Guide (For New Users)](#-quick-start-guide-for-new-users)
  - [1. Prerequisites](#1-prerequisites)
  - [2. Backend Setup (FastAPI)](#2-backend-setup-fastapi)
  - [3. Frontend Setup (Next.js)](#3-frontend-setup-nextjs)
  - [4. Environment Variables](#4-environment-variables)
- [📡 API Reference](#-api-reference)
  - [`GET /health`](#get-health)
  - [`POST /ask`](#post-ask)
- [🧪 Testing & Offline Evaluation](#-testing--offline-evaluation)
- [📑 Core System Contracts](#-core-system-contracts)
- [📈 Status & Roadmap](#-status--roadmap)
- [📜 License](#-license)

---

## 📖 Overview

Welcome to **MausamPraman** (Hindi: *Weather Proof/Verification*)!

Weather forecasts and AI-generated weather responses often suffer from two major problems:
1. **Model Divergence & Uncertainty**: A single forecast model might predict rain while others predict dry weather, misleading farmers and travelers without communicating forecast uncertainty.
2. **AI Hallucinations**: Large Language Models (LLMs) used in weather apps can invent temperatures, alter official severe weather warnings, or misquote precipitations.

> [!IMPORTANT]
> **The Core Philosophy of MausamPraman**
> **Deterministic code makes ALL decisions; LLM is ONLY allowed to reword.**
> - **Fact Retrieval & Calculation**: Handled by Python deterministic engines (Open-Meteo forecasts, 3-model divergence metrics, active district warning lookup, rule-based crop advisories).
> - **Confidence & Safety**: Evaluated deterministically with strict Grade bands (**A, B, C, D**).
> - **LLM Role**: Strictly constrained to natural language formatting (via Sarvam AI). If the LLM output fails grounding validation or times out, the system seamlessly falls back to pre-validated deterministic templates.

---

## 🎯 Key Highlights & Principles

> [!TIP]
> **Why MausamPraman is Different**
> - 🛡️ **Zero Hallucination Guarantee**: Every LLM draft is passed through a **Deterministic Grounding Validator**. Numerical values or warning levels not present in raw forecast data are immediately blocked.
> - 📊 **Multi-Model Divergence Grade**: Evaluates agreement across 3 weather models to calculate forecast uncertainty (Grade A = high agreement, Grade D = high divergence / uncertainty).
> - 🌾 **Agricultural Advisories**: Contextual guidance for crops (e.g. Grape farming in Nashik) linked directly to confidence grade thresholds.
> - ⚡ **Offline Resilient Architecture**: Supports full offline test execution (`MAUSAM_OFFLINE=1`) with stubbed geocoding and mock weather divergence scenarios.
> - 🌐 **Bilingual Support**: Native English and Hindi templates with Sarvam AI phrasing fallback.

---

## 🧱 System Architecture & Data Flow

Below is the request-response workflow inside MausamPraman:

```
                          ┌───────────────────────────┐
                          │   User Query (HTTP POST)   │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │    Intent Classification  │
                          │ (weather, rain, warning,  │
                          │   confidence, advice)     │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │    Location Resolution    │
                          │   (IN Geocoder / Fallback) │
                          └─────────────┬─────────────┘
                                        │
                         ┌──────────────┴──────────────┐
                         ▼                             ▼
              ┌────────────────────┐        ┌────────────────────┐
              │ Weather Forecast & │        │ District Warning   │
              │ 3-Model Divergence │        │ Store Verification │
              └─────────┬──────────┘        └─────────┬──────────┘
                        │                             │
                        └──────────────┬──────────────┘
                                       │
                                       ▼
                          ┌───────────────────────────┐
                          │   Deterministic Grade     │
                          │ Engine (Grades A / B / C / D)│
                          └─────────────┬─────────────┘
                                       │
                        ┌──────────────┴──────────────┐
                        ▼                             ▼
             ┌─────────────────────┐       ┌─────────────────────┐
             │ Crop Advisory Rules │       │ Sarvam LLM Phrasing │
             │  (Grape, Stage, etc)│       │ / Template Fallback │
             └──────────┬──────────┘       └──────────┬──────────┘
                        │                             │
                        └──────────────┬──────────────┘
                                       │
                                       ▼
                          ┌───────────────────────────┐
                          │ Grounding Check Validator │
                          │(Must match forecast data) │
                          └─────────────┬─────────────┘
                                       │
                                       ▼
                          ┌───────────────────────────┐
                          │   Grounded JSON Response  │
                          └───────────────────────────┘
```

---

## 📊 Agreement Bands & Confidence Matrix

MausamPraman uses 3-model precipitation/temperature divergence to calculate agreement confidence. This grade reflects forecast agreement across numerical models—**it is not a statistical probability**.

| Grade | Description | Model Spread | Warning Override | System Behavior |
| :---: | :--- | :---: | :---: | :--- |
| **Grade A** | **Strong Agreement** | Spread $\le 1.0\text{ mm}$ | No active warning | Strong advisories allowed, high trust wording |
| **Grade B** | **Moderate Agreement** | Spread $\le 3.0\text{ mm}$ | No active warning | Moderate advisories allowed, standard trust wording |
| **Grade C** | **High Spread / Divergence** | Spread $> 3.0\text{ mm}$ | No active warning | Caution advisory (`watch_only`), uncertainty highlighted |
| **Grade D** | **Severe Uncertainty / Warning** | Any | Active Non-Green Warning OR Service Down | Forced Grade D override. Strict caution enforced |

> [!WARNING]
> **Active Severe Warnings Override Grade**: If a district has an active Orange or Red warning issued, the confidence grade is automatically downgraded to **D** regardless of model spread, ensuring user safety comes first.

---

## 🚀 Quick Start Guide (For New Users)

Follow these simple steps to run MausamPraman on your local machine.

### 1. Prerequisites

Make sure you have the following installed:
- **Python 3.10+**
- **Node.js 18+** & `npm`
- **Git**

---

### 2. Backend Setup (FastAPI)

1. Open your terminal and navigate to the `mausampraman` folder:
   ```bash
   cd mausampraman
   ```

2. Create and activate a Python virtual environment (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the backend server:
   ```bash
   uvicorn api.main:app --reload --port 8000
   ```
   *The backend will now be running at `http://localhost:8000`.*

5. Verify backend health:
   ```bash
   curl http://localhost:8000/health
   # Output: {"status":"ok"}
   ```

---

### 3. Frontend Setup (Next.js)

1. Open a new terminal window and navigate to the frontend directory:
   ```bash
   cd mausampraman/web
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Next.js development server:
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
   ```

4. Open your browser and visit:
   `http://localhost:3000`

---

### 4. Environment Variables

Create a `.env` file inside `mausampraman/` directory if you wish to configure live LLM phrasing or production CORS origins:

```env
# Optional: Sarvam AI Key for live LLM phrasing (if omitted, system uses template fallback)
SARVAM_API_KEY=your_sarvam_api_key_here

# Optional: Frontend origin for CORS restriction in production
FRONTEND_ORIGIN=http://localhost:3000
```

---

## 📡 API Reference

### `GET /health`
Returns system status.
- **Response**:
  ```json
  {
    "status": "ok"
  }
  ```

---

### `POST /ask`
Submits a weather query with optional parameters for crop guidance and language.

#### Request Headers:
`Content-Type: application/json`

#### Request Body Parameters:
| Parameter | Type | Required | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| `query` | `string` | **Yes** | `"Nashik weather"` | Free text question (e.g., "Will it rain in Nashik?", "Grape flowering advice Nashik") |
| `lang` / `language` | `string` | No | `"en"` | Language code (`"en"` or `"hi"`) |
| `location` | `string` | No | `null` | Explicit location override |
| `crop` | `string` | No | `null` | Crop type (e.g., `"grape"`) |
| `stage` | `string` | No | `null` | Crop stage (e.g., `"flowering"`, `"fruit-set"`, `"veraison"`, `"harvest"`) |

#### Sample Request (`curl`):
```bash
curl -X POST http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Is rain expected in Nashik for grape flowering?",
    "lang": "en"
  }'
```

#### Sample Response (`200 OK`):
```json
{
  "answer": "Nashik: 0.0mm rain expected. Green warning status. Agreement A.",
  "intent": {
    "intent": "agriculture_advice",
    "confidence": "high",
    "signals": ["grape", "flowering"]
  },
  "confidence": {
    "grade": "A",
    "warning_override": false,
    "spread_mm": 0.2,
    "skill_prior": 0.85,
    "drivers": {
      "spread_mm": 0.2
    }
  },
  "provenance": {
    "forecast_source": "open-meteo",
    "warning_source": "warnings-store",
    "grounded": true
  },
  "advisory": {
    "crop": "grape",
    "stage": "flowering",
    "rule_id": "GRAPE_FLOWERING_DRY_A",
    "advice_en": "Dry conditions during flowering favor healthy fruit-set. Avoid unnecessary irrigation.",
    "strength": "strong",
    "safe": true
  },
  "location": {
    "name": "Nashik",
    "lat": 19.9975,
    "lon": 73.7898,
    "state": "Unknown",
    "country": "Unknown"
  },
  "warning": {
    "district": "nashik",
    "severity": "green",
    "headline": "No active warning",
    "body": "",
    "issued_at": "2025-01-01T00:00:00Z",
    "capture_date": "2025-01-01",
    "status": "no_warning_confirmed"
  },
  "forecast": {
    "temp_c": 28.5,
    "humidity_pct": 45,
    "wind_kph": 12.0,
    "precip_mm": 0.0,
    "condition": "Clear",
    "source": "open-meteo"
  },
  "daily": null
}
```

---

## 🧪 Testing & Offline Evaluation

MausamPraman includes a robust test suite supporting offline validation and golden question evaluation.

### Run Unit Tests (Offline Suite)
```bash
cd mausampraman
PYTHONPATH=. python3 -m pytest -q
```

### Run Network-Free Proof Test
```bash
cd mausampraman
MAUSAM_OFFLINE=1 PYTHONPATH=. python3 -m pytest -q
```

### Run Integrated Evaluation Suite
```bash
cd mausampraman
python3 eval/run_all.py
```

### Run Live Golden Questions Benchmark (Requires running backend)
```bash
cd mausampraman
python3 eval/run_golden_set.py
```

---

## 📑 Core System Contracts

For detailed API function contracts, module boundaries, and internal specifications, refer to [mausampraman/CONTRACTS.md](mausampraman/CONTRACTS.md).

For deployment guides on Render and Vercel/Static hosts, refer to [mausampraman/DEPLOY.md](mausampraman/DEPLOY.md).

---

## 📈 Status & Roadmap

> [!NOTE]
> MausamPraman is currently a **prototype with measured claims**. We believe in total transparency regarding what works today vs what is deferred.

| Feature Area | Implementation Status | Details |
| :--- | :---: | :--- |
| **Intent Routing** | 🟩 **Implemented** | 6 intent categories (current weather, rain, warning, trust explanation, agriculture advice, unsupported). |
| **Location Resolution** | 🟩 **Implemented** | Preference for Indian locations (`geocode_in`), fallback handling. |
| **Open-Meteo Integration** | 🟩 **Implemented** | Real-time forecast + daily metrics + 3-model divergence scenario engine. |
| **District Warning Store** | 🟩 **Implemented** | File-backed store with 4 explicit states (`active_warning`, `no_warning_confirmed`, `warning_data_unavailable`, `district_not_covered`). |
| **Agreement Grading** | 🟩 **Implemented** | Deterministic Bands A, B, C, D with spread metrics and warning overrides. |
| **Agricultural Advisories** | 🟩 **Implemented** | Grape advisory rules engine (opt-in). |
| **Grounding Validator** | 🟩 **Implemented** | Checks LLM output against raw forecast facts before sending response. |
| **LLM Phrasing** | 🟨 **Partial** | Works via Sarvam AI API when key & budget permit; falls back to templates seamlessly. |
| **Hindi Translation** | 🟨 **Partial** | Pipeline & template translations exist; human prose quality review recommended. |
| **Real IMD Live Feed** | 🟦 **Deferred** | Currently uses district warning file store. Real live IMD scraper planned. |
| **Geolocation & NER** | 🟦 **Deferred** | Advanced location NER & browser geolocation API queued for v2. |

---

## 📜 License

This project is licensed under the MIT License.
