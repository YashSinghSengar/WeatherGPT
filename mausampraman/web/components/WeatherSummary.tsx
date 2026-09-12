import type { AskResponse } from "../lib/api";

function Cell({ k, v }: { k: string; v: string }) {
  return (<div className="summary-cell"><div className="v">{v}</div><div className="k">{k}</div></div>);
}

export default function WeatherSummary({ data }: { data: AskResponse }) {
  const f = data.forecast;
  const cells = [
    <Cell key="t" k="Temperature" v={`${f.temp_c}°C`} />,
    <Cell key="c" k="Condition" v={f.condition.replace(/_/g, " ")} />,
    <Cell key="r" k="Rain" v={`${f.precip_mm} mm`} />,
  ];
  if (f.humidity_pct) cells.push(<Cell key="h" k="Humidity" v={`${f.humidity_pct}%`} />);
  if (f.wind_kph) cells.push(<Cell key="w" k="Wind" v={`${f.wind_kph} km/h`} />);
  return (
    <section className="card" aria-label="Weather summary">
      <h3>{data.location.name}</h3>
      <p className="muted">{data.location.lat.toFixed(2)}°N, {data.location.lon.toFixed(2)}°E · {f.source} · horizon 2 days</p>
      <div className="summary-grid">{cells}</div>
    </section>
  );
}
