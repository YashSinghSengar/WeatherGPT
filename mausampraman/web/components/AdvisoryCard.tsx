import type { AskResponse } from "../lib/api";

export default function AdvisoryCard({ data }: { data: AskResponse }) {
  const a = data.advisory;
  const lowTrust = data.confidence.grade === "D" || data.confidence.warning_override;
  return (
    <section className="card" aria-label="Advisory">
      <h3>Advisory — {a.crop}, {a.stage}</h3>
      {lowTrust && (
        <p className="muted"><strong>Caution:</strong> confidence is {data.confidence.grade}
        {data.confidence.warning_override ? " with an active warning" : ""}. This is watch-only guidance, not confident advice.</p>
      )}
      <p><strong>Action:</strong> {a.advice_en}</p>
      <p><strong>Strength:</strong> {a.strength}</p>
      <p className="muted"><strong>Rationale rule:</strong> {a.rule_id}</p>
    </section>
  );
}
