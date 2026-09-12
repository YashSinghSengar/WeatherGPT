import type { Confidence, Warning } from "../lib/api";

const STATE_LABEL: Record<string, string> = {
  active_warning: "Official warning active",
  no_warning_confirmed: "No active warning reported by the available source",
  warning_data_unavailable: "Warning status unavailable",
  district_not_covered: "Warning coverage unavailable for this location",
};

export function WarningState({ warning }: { warning: Warning }) {
  if (warning.status === "active_warning") return null;
  return <p className="quiet">{STATE_LABEL[warning.status] || warning.status}.</p>;
}

export default function WarningCard({ confidence, warning }: { confidence: Confidence; warning: Warning }) {
  if (warning.status !== "active_warning") return null;
  return (
    <section className="card warn-card" role={confidence.warning_override ? "alert" : "status"} aria-label="Official warning">
      <h3>⚠ Official warning — {warning.severity}</h3>
      <p><strong>{warning.headline}</strong></p>
      {warning.body && <p>{warning.body}</p>}
      <p className="muted">Issued {warning.issued_at} · captured {warning.capture_date}</p>
    </section>
  );
}
