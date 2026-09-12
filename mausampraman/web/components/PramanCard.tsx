import type { Advisory, Confidence, Forecast, Location, Warning } from "../lib/api";
import GradeBadge from "./GradeBadge";

export interface PramanData {
  location: Location;
  forecast: Forecast;
  confidence: Confidence;
  warning: Warning;
  advisory: Advisory | null;
  provenance: { forecast_source: string; warning_source: string; grounded: boolean };
}

export default function PramanCard({ data }: { data: PramanData }) {
  return (
    <section className="card" aria-label="Praman Card: evidence behind this answer">
      <h3>Praman Card — evidence behind this answer</h3>
      <dl className="kv">
        <dt>Location</dt><dd>{data.location.name}</dd>
        <dt>Location resolved to</dt><dd>{data.location.lat}, {data.location.lon}</dd>
        <dt>Forecast</dt><dd>{data.forecast.temp_c}°C, {data.forecast.condition}, rain {data.forecast.precip_mm} mm</dd>
        <dt>Model spread</dt><dd>{data.confidence.spread_mm} mm across GFS / ECMWF / ICON runs</dd>
        <dt>Agreement</dt><dd><GradeBadge grade={data.confidence.grade} /></dd>
        <dt>Warning</dt><dd>{data.warning.severity} — {data.warning.headline}</dd>
        {data.advisory && (<><dt>Advisory rule</dt><dd>{data.advisory.rule_id} ({data.advisory.strength})</dd></>)}
        <dt>Sources</dt><dd>{data.provenance.forecast_source} · {data.provenance.warning_source} · grounded: {String(data.provenance.grounded)}</dd>
      </dl>
    </section>
  );
}
