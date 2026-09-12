"use client";
const EXAMPLES = ["Will it rain tonight in Nashik?", "Should I irrigate my grapes today?", "Is there a weather warning for Nashik?", "How confident is the Nashik forecast?"];

export default function EmptyState({ onPick }: { onPick: (q: string, lang: string) => void }) {
  return (
    <div className="card">
      <h3>What can MausamPraman answer?</h3>
      <p className="muted">Rain and temperature outlooks, grape advisories, active warnings, and how much to trust each answer — in English or Hindi.</p>
      <div className="chips">
        {EXAMPLES.map((q) => (<button key={q} className="chip" onClick={() => onPick(q, "en")}>{q}</button>))}
      </div>
    </div>
  );
}
