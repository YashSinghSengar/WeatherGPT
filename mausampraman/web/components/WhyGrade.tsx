import type { AskResponse } from "../lib/api";

export default function WhyGrade({ data }: { data: AskResponse }) {
  const c = data.confidence;
  const items = [`Model spread ${c.spread_mm} mm across GFS / ECMWF / ICON runs`];
  if (data.confidence.warning_override) items.push(`Active ${data.warning.severity} warning forces grade D`);
  items.push(`Skill prior ${c.skill_prior} (verification history table, currently empty)`);
  return (
    <details className="why">
      <summary>Why this grade?</summary>
      <ul>{items.map((s) => (<li key={s}>{s}</li>))}</ul>
    </details>
  );
}
