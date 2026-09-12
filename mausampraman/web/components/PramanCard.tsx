import type { AskResponse } from "../lib/api";
import GradeBadge from "./GradeBadge";

export default function PramanCard({ data }: { data: AskResponse }) {
  return (
    <section className="card" aria-label="Praman Card: evidence behind this answer">
      <h3>Praman Card — evidence behind this answer</h3>
      <dl className="kv">
        <dt>Location</dt><dd>{data.location.name}</dd>
        <dt>Location resolved to</dt><dd>{data.location.lat}, {data.location.lon}</dd>
        <dt>Forecast</dt><dd>{data.forecast.temp_c}°C, {data.forecast.condition}, rain {data.forecast.precip_mm} mm</dd>
        <dt>Model spread</dt><dd>{data.confidence.spread_mm} mm across GFS / ECMWF / ICON runs</dd>
        <dt>Confidence</dt><dd><GradeBadge grade={data.confidence.grade} /></dd>
        <dt>Warning</dt><dd>{data.warning.severity} — {data.warning.headline}</dd>
        <dt>Advisory rule</dt><dd>{data.advisory.rule_id} ({data.advisory.strength})</dd>
        <dt>Sources</dt><dd>{data.provenance.forecast_source} · {data.provenance.warning_source} · grounded: {String(data.provenance.grounded)}</dd>
      </dl>
    </section>
  );
}
