import type { DailyPeriod } from "../lib/api";

const NAMES = ["Today", "Tomorrow"];

export default function DailyForecast({ daily }: { daily: DailyPeriod[] }) {
  return (
    <section className="card" aria-label="Short forecast">
      <h3>Next {daily.length} days</h3>
      <div className="summary-grid">
        {daily.map((p, i) => (
          <div key={p.date} className="summary-cell">
            <div className="k">{NAMES[i] || p.date}</div>
            <div className="v">{p.temp_max_c !== null && p.temp_min_c !== null ? `${p.temp_max_c}° / ${p.temp_min_c}°` : "—"}</div>
            <div className="k">{p.date}</div>
            <div className="k">{p.condition ? p.condition.replace(/_/g, " ") : "—"}</div>
            <div className="k">{p.precip_mm !== null ? `${p.precip_mm} mm` : "—"}{p.precip_prob_pct !== null ? ` · ${p.precip_prob_pct}%` : ""}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
