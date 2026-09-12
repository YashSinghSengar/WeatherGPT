import GradeBadge from "../../components/GradeBadge";

const STEPS = [
  ["User query", "A plain question in English or Hindi."],
  ["Location resolution", "The place name is resolved to coordinates."],
  ["Weather data", "Current conditions from Open-Meteo, three models."],
  ["Official warning lookup", "Stored district warnings; orange/red override all."],
  ["Confidence / trust engine", "Model disagreement becomes a deterministic A–D grade."],
  ["Grounded advisory rules", "Grape-stage rules matched to the measured spread."],
  ["LLM phrasing", "AI words the decided answer — nothing more."],
  ["Final answer", "Answer plus grade, evidence, and sources."],
];

export default function HowItWorks() {
  return (
    <>
      <h1>How it works</h1>
      <div className="notice"><strong>The AI phrases the answer. It does not decide the forecast confidence.</strong> Grades, warnings, and advisories are computed by deterministic code; the language model only chooses words, under strict validation.</div>
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
