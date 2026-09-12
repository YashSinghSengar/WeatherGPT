import type { AskResponse } from "../lib/api";

export default function WarningCard({ data }: { data: AskResponse }) {
  if (!data.confidence.warning_override) return null;
  return (
    <section className="card warn-card" role="alert" aria-label="Official warning">
      <h3>⚠ Official warning — {data.warning.severity}</h3>
      <p><strong>{data.warning.headline}</strong></p>
      {data.warning.body && <p>{data.warning.body}</p>}
      <p className="muted">Issued {data.warning.issued_at} · captured {data.warning.capture_date}</p>
    </section>
  );
}
