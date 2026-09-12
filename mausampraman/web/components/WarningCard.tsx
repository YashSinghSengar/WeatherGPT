import type { Confidence, Warning } from "../lib/api";

export default function WarningCard({ confidence, warning }: { confidence: Confidence; warning: Warning }) {
  if (!confidence.warning_override) return null;
  return (
    <section className="card warn-card" role="alert" aria-label="Official warning">
      <h3>⚠ Official warning — {warning.severity}</h3>
      <p><strong>{warning.headline}</strong></p>
      {warning.body && <p>{warning.body}</p>}
      <p className="muted">Issued {warning.issued_at} · captured {warning.capture_date}</p>
    </section>
  );
}
