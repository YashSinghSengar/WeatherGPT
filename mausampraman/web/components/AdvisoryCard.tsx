import type { Advisory, Confidence } from "../lib/api";

export default function AdvisoryCard({ advisory, confidence }: { advisory: Advisory; confidence: Confidence }) {
  const lowTrust = confidence.grade === "D" || confidence.warning_override;
  return (
    <section className="card" aria-label="Advisory">
      <h3>Advisory — {advisory.crop}, {advisory.stage}</h3>
      {lowTrust && (
        <p className="muted"><strong>Caution:</strong> agreement is {confidence.grade}
        {confidence.warning_override ? " with an active warning" : ""}. This is watch-only guidance, not confident advice.</p>
      )}
      <p><strong>Action:</strong> {advisory.advice_en}</p>
      <p><strong>Strength:</strong> {advisory.strength}</p>
      <p className="muted"><strong>Rationale rule:</strong> {advisory.rule_id}</p>
    </section>
  );
}
