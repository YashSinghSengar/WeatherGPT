"use client";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { askBackend, type AskResponse } from "../../lib/api";
import EmptyState from "../../components/EmptyState";
import ErrorCard from "../../components/ErrorCard";
import LoadingSkeleton from "../../components/LoadingSkeleton";
import GradeBadge from "../../components/GradeBadge";
import PramanCard from "../../components/PramanCard";
import AdvisoryCard from "../../components/AdvisoryCard";
import WarningCard from "../../components/WarningCard";
import WeatherSummary from "../../components/WeatherSummary";
import WhyGrade from "../../components/WhyGrade";

const STAGES = ["flowering", "fruit-set", "veraison", "harvest"];
const OCCUPATIONS = ["General", "Farmer", "Fisher", "Outdoor work"];

export default function Chat() {
  return (
    <Suspense>
      <ChatInner />
    </Suspense>
  );
}

function ChatInner() {
  const params = useSearchParams();
  const [location, setLocation] = useState("");
  const [query, setQuery] = useState("");
  const [lang, setLang] = useState("en");
  const [mode, setMode] = useState<"general" | "agri">("general");
  const [crop, setCrop] = useState("grape");
  const [stage, setStage] = useState("veraison");
  const [occupation, setOccupation] = useState("General");
  const [data, setData] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const loc = params.get("loc");
    if (loc) { setLocation(loc); run(loc, `Weather in ${loc}`, lang, mode, crop, stage); }
    const saved = localStorage.getItem("mp-lang");
    if (saved === "en" || saved === "hi") setLang(saved);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function pickLang(l: string) { setLang(l); localStorage.setItem("mp-lang", l); }

  async function run(loc: string, q: string, l: string, m: string, c: string, s: string) {
    const question = q.trim() || (loc.trim() ? `Weather in ${loc.trim()}` : "");
    if (!question || loading) return;
    setLoading(true); setError(""); setData(null);
    try {
      setData(await askBackend({ query: question, language: l, location: loc.trim() || undefined, crop: m === "agri" ? c : "grape", stage: s }));
    } catch {
      setError("Unable to reach MausamPraman right now. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const agri = mode === "agri";
  const cropSupported = crop === "grape";

  return (
    <>
      <h1>Ask MausamPraman</h1>
      <form onSubmit={(e) => { e.preventDefault(); run(location, query, lang, mode, crop, stage); }}>
        <label htmlFor="loc">Location</label>
        <div className="chat-form">
          <input id="loc" type="text" value={location} onChange={(e) => setLocation(e.target.value)}
            placeholder="Bhopal, Nashik, Delhi…" disabled={loading} />
        </div>
        <label htmlFor="q">Question</label>
        <div className="chat-form">
          <input id="q" type="text" value={query} onChange={(e) => setQuery(e.target.value)}
            placeholder="Will it rain tonight?" disabled={loading} />
        </div>
        <div className="seg" role="group" aria-label="Mode">
          {(["general", "agri"] as const).map((m) => (
            <button key={m} type="button" aria-pressed={mode === m} onClick={() => setMode(m)}>
              {m === "general" ? "General Weather" : "Agriculture"}
            </button>
          ))}
        </div>
        {agri && (
          <div className="chat-form">
            <label htmlFor="crop">Crop</label>
            <select id="crop" value={crop} onChange={(e) => setCrop(e.target.value)} disabled={loading}>
              <option value="grape">Grape (supported)</option>
              <option value="wheat">Wheat (not yet supported)</option>
              <option value="rice">Rice (not yet supported)</option>
            </select>
            <label htmlFor="stage">Stage</label>
            <select id="stage" value={stage} onChange={(e) => setStage(e.target.value)} disabled={loading}>
              {STAGES.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
          </div>
        )}
        <div className="chat-form">
          <label htmlFor="occ">Context</label>
          <select id="occ" value={occupation} onChange={(e) => setOccupation(e.target.value)} disabled={loading}>
            {OCCUPATIONS.map((o) => (<option key={o} value={o}>{o}</option>))}
          </select>
          <label htmlFor="lang">Language</label>
          <select id="lang" value={lang} onChange={(e) => pickLang(e.target.value)} disabled={loading}>
            <option value="en">English</option>
            <option value="hi">हिंदी</option>
          </select>
          <button className="btn" type="submit" disabled={loading || (!query.trim() && !location.trim())}>
            {loading ? "Asking…" : "Ask"}
          </button>
        </div>
      </form>
      {occupation !== "General" && occupation !== "Farmer" && (
        <p className="quiet">No dedicated {occupation.toLowerCase()} rules yet — showing general weather, warnings, and trust.</p>
      )}
      {loading && <LoadingSkeleton />}
      {error && !loading && <ErrorCard message={error} onRetry={() => run(location, query, lang, mode, crop, stage)} />}
      {!loading && !error && !data && <EmptyState onAsk={(loc, q) => { setLocation(loc); setQuery(q); run(loc, q, lang, mode, crop, stage); }} />}
      {!loading && !error && data && (
        <>
          {data.confidence && data.warning && <WarningCard confidence={data.confidence} warning={data.warning} />}
          {data.confidence && data.warning && !data.confidence.warning_override && data.warning.severity === "green" && (
            <p className="quiet">No active warning in the local warning store. This covers stored districts only, not all official warnings.</p>
          )}
          <section className="card" aria-label="Answer">
            <p className="answer-text">{data.answer}</p>
            {data.confidence && (
              <>
                <GradeBadge grade={data.confidence.grade} />
                {data.warning && <WhyGrade confidence={data.confidence} warning={data.warning} />}
              </>
            )}
          </section>
          {data.forecast && data.location && <WeatherSummary location={data.location} forecast={data.forecast} />}
          {agri && data.advisory && data.confidence && <AdvisoryCard advisory={data.advisory} confidence={data.confidence} />}
          {agri && !data.advisory && <p className="quiet">{cropSupported ? "Specific grounded guidance is unavailable for this case." : `Grounded guidance for ${crop} is not currently available. Only grape rules exist.`}</p>}
          {data.forecast && data.location && data.confidence && data.warning && <PramanCard data={{ location: data.location, forecast: data.forecast, confidence: data.confidence, warning: data.warning, advisory: data.advisory, provenance: data.provenance }} />}
        </>
      )}
    </>
  );
}
