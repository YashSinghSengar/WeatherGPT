import type { Confidence, Warning } from "../lib/api";

export default function WhyGrade({ confidence, warning }: { confidence: Confidence; warning: Warning }) {
  const items = [`Model spread ${confidence.spread_mm} mm across GFS / ECMWF / ICON runs`];
  if (confidence.warning_override) items.push(`Active ${warning.severity} warning forces grade D`);
  items.push(`Skill prior ${confidence.skill_prior} (verification history table, currently empty)`);
  return (
    <details className="why">
      <summary>Why this grade?</summary>
      <ul>{items.map((s) => (<li key={s}>{s}</li>))}</ul>
    </details>
  );
}
