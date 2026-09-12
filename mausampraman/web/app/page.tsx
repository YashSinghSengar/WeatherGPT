import Link from "next/link";
import type { ReactNode } from "react";
import GradeBadge from "../components/GradeBadge";

const FLOW = [
  ["Weather Data", "Open-Meteo forecasts, three global models"],
  ["Forecast Agreement", "How much the models disagree, in mm of rain"],
  ["Trust / Confidence", "Deterministic A–D grade, never decided by AI"],
  ["Impact Advisory", "Grape-stage rules matched to the disagreement"],
  ["Human-Friendly Answer", "AI phrasing only — facts stay fixed"],
];

const WHY = [
  ["Forecast confidence", "Every answer carries an A–D trust grade computed from real model disagreement."],
  ["Warning-first safety", "An active warning overrides everything: grade D, caution-first display."],
  ["Grounded advisories", "Advice comes from fixed grape-stage rules, matched to measured disagreement — never invented."],
  ["English + Hindi", "Ask and read answers in English or Hindi."],
];

export default function Home() {
  return (
    <>
      <section className="hero">
        <h1>Weather intelligence you can trust.</h1>
        <p>MausamPraman combines weather forecasts, forecast confidence, official warnings, and grounded advisory rules before giving you an answer — so you know not just what the weather may do, but how much to trust it.</p>
        <div className="cta-row">
          <Link href="/chat" className="btn">Ask MausamPraman</Link>
          <Link href="/how-it-works" className="btn btn-secondary">How it works</Link>
        </div>
      </section>
      <section aria-label="Core idea">
        <h2>From sky data to trusted advice</h2>
        <ol className="pipeline">
          {FLOW.map(([t, s]) => (<li key={t}>{t}<span>{s}</span></li>)).reduce<ReactNode[]>((acc, li, i) => (i ? [...acc, <div key={`a${i}`} className="pipe-arrow" aria-hidden="true">↓</div>, li] : [li]), [])}
        </ol>
      </section>
      <section aria-label="Why MausamPraman">
        <h2>Why MausamPraman?</h2>
        <div className="grid">
          {WHY.map(([t, s]) => (<div key={t} className="card"><h3>{t}</h3><p className="muted">{s}</p></div>))}
        </div>
      </section>
      <section aria-label="How trust works">
        <h2>How trust works</h2>
        <p className="muted">Grades describe measured model agreement, not probabilities.</p>
        <div className="grid">
          <div className="card"><GradeBadge grade="A" /><p>High confidence — models agree closely.</p></div>
          <div className="card"><GradeBadge grade="B" /><p>Moderate confidence — some disagreement.</p></div>
          <div className="card"><GradeBadge grade="C" /><p>Low confidence — wide disagreement.</p></div>
          <div className="card"><GradeBadge grade="D" /><p>Insufficient confidence — or an active warning.</p></div>
        </div>
      </section>
      <section aria-label="Built for Indian users">
        <h2>Built for Indian users</h2>
        <p>English and Hindi answers, focused on the farming weather decisions grape growers face every season.</p>
      </section>
      <section className="card" aria-label="Final call to action">
        <h2>Ask about your weather</h2>
        <Link href="/chat" className="btn">Ask MausamPraman</Link>
      </section>
    </>
  );
}
