import type { Forecast, Location } from "../lib/api";

function Cell({ k, v }: { k: string; v: string }) {
  return (<div className="summary-cell"><div className="v">{v}</div><div className="k">{k}</div></div>);
}

export default function WeatherSummary({ location, forecast }: { location: Location; forecast: Forecast }) {
  const cells = [
    <Cell key="t" k="Temperature" v={`${forecast.temp_c}°C`} />,
    <Cell key="c" k="Condition" v={forecast.condition.replace(/_/g, " ")} />,
    <Cell key="r" k="Rain" v={`${forecast.precip_mm} mm`} />,
  ];
  if (forecast.humidity_pct) cells.push(<Cell key="h" k="Humidity" v={`${forecast.humidity_pct}%`} />);
  if (forecast.wind_kph) cells.push(<Cell key="w" k="Wind" v={`${forecast.wind_kph} km/h`} />);
  if (forecast.precip_prob_pct !== null && forecast.precip_prob_pct !== undefined) cells.push(<Cell key="p" k="Rain chance" v={`${forecast.precip_prob_pct}%`} />);
  return (
    <section className="card" aria-label="Weather summary">
      <h3>{location.name}</h3>
      <p className="muted">{location.lat.toFixed(2)}°N, {location.lon.toFixed(2)}°E · {forecast.source} · horizon 2 days</p>
      <div className="summary-grid">{cells}</div>
    </section>
  );
}
