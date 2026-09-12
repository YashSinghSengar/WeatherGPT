import GradeBadge from "../../components/GradeBadge";

const STEPS = [
  ["Resolve the location", "Place name or explicit selection becomes coordinates."],
  ["Collect weather data", "Current conditions from Open-Meteo, three models."],
  ["Check warnings", "Stored district warnings; severe ones override everything."],
  ["Compare forecast signals", "Yesterday's per-model rain totals become a disagreement spread."],
  ["Assign confidence", "Spread, data age, and horizon map to a deterministic A–D grade."],
  ["Apply grounded rules", "Crop-stage rules fire only on measured spread bands."],
  ["Phrase the result", "A language model words the decided answer under strict validation."],
  ["Show provenance", "Coordinates, sources, drivers, and citations ship with the answer."],
];

export default function HowItWorks() {
  return (
    <>
      <h1>How it works</h1>
      <div className="notice"><strong>LLM does not decide the weather verdict.</strong> Grades, warnings, and advisories are computed by deterministic code; the language model only chooses words, under strict validation.</div>
      <div className="notice"><strong>Warnings override normal advice.</strong> An active warning forces grade D, watch-only guidance, and a dominant warning display.</div>
      <ol className="steps">
        {STEPS.map(([t, s]) => (<li key={t}><strong>{t}</strong> — {s}</li>))}
      </ol>
      <h2>Confidence grades</h2>
      <div className="grid">
        <div className="card"><GradeBadge grade="A" /><p>High confidence.</p></div>
        <div className="card"><GradeBadge grade="B" /><p>Moderate confidence.</p></div>
        <div className="card"><GradeBadge grade="C" /><p>Low confidence.</p></div>
        <div className="card"><GradeBadge grade="D" /><p>Insufficient confidence, or warning override.</p></div>
      </div>
    </>
  );
}
