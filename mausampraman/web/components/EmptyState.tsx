"use client";
const EXAMPLES: [string, string][] = [
  ["Bhopal", "Will it rain tonight?"],
  ["Nashik", "Should I irrigate my grapes today?"],
  ["Delhi", "What is the temperature?"],
  ["Mumbai", "Is rain expected?"],
];

export default function EmptyState({ onAsk }: { onAsk: (loc: string, q: string) => void }) {
  return (
    <div className="card">
      <h3>What can MausamPraman answer?</h3>
      <p className="muted">Pick a location and ask — rain outlooks, warnings, forecast trust, and optional grape advisories, in English or Hindi.</p>
      <div className="chips">
        {EXAMPLES.map(([loc, q]) => (<button key={loc} className="chip" onClick={() => onAsk(loc, q)}>{loc}: {q}</button>))}
      </div>
    </div>
  );
}
