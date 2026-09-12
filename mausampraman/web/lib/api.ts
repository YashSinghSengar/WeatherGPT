export interface Confidence { grade: string; warning_override: boolean; spread_mm: number; skill_prior: number; drivers: { spread_mm: number }; }
export interface Advisory { crop: string; stage: string; rule_id: string; advice_en: string; advice_hi: string; citation: string; strength: string; safe: boolean; }
export interface Location { name: string; lat: number; lon: number; state: string; country: string; }
export interface Warning { district: string; severity: string; headline: string; body: string; issued_at: string; capture_date: string; }
export interface Forecast { temp_c: number; humidity_pct: number; wind_kph: number; precip_mm: number; condition: string; source: string; lat: number; lon: number; }
export interface AskResponse { answer: string; confidence: Confidence; provenance: { forecast_source: string; warning_source: string; grounded: boolean }; advisory: Advisory; location: Location; warning: Warning; forecast: Forecast; }

export interface AskRequest { query: string; language: string; location?: string; crop?: string; stage?: string; }

export async function askBackend(req: AskRequest): Promise<AskResponse> {
  const base = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 90000);
  const url = `${base}/ask`;
  const body = { query: req.query, language: req.language, location: req.location || undefined, crop: req.crop || "grape", stage: req.stage || "veraison" };
  try {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    if (!r.ok) throw new Error(`backend ${r.status}`);
    const d = await r.json();
    if (!d || typeof d.answer !== "string" || !d.confidence || !d.location) throw new Error("bad shape");
    return d as AskResponse;
  } finally {
    clearTimeout(timer);
  }
}
