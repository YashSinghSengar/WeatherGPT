import Link from "next/link";

export default function Home() {
  return (
    <>
      <section className="hero">
        <h1>MausamPraman</h1>
        <p className="tagline">Weather intelligence you can trust.</p>
        <p>Forecasts are useful. Knowing how much to trust them is better.</p>
        <div className="cta-row">
          <Link href="/chat" className="btn">Ask MausamPraman</Link>
          <Link href="/how-it-works" className="btn btn-secondary">How it works</Link>
        </div>
      </section>
      <section aria-label="Product flow">
        <div className="flow">
          <span>Weather data</span><span aria-hidden="true">→</span>
          <span>Forecast trust</span><span aria-hidden="true">→</span>
          <span>Grounded advisory</span><span aria-hidden="true">→</span>
          <span>Clear answer</span>
        </div>
      </section>
      <section aria-label="Capabilities">
        <h2>What it does</h2>
        <div className="grid">
          <div className="card"><h3>Weather</h3><p className="muted">Current conditions for any resolvable location.</p></div>
          <div className="card"><h3>Warnings</h3><p className="muted">Stored warnings override normal advice, visibly.</p></div>
          <div className="card"><h3>Forecast agreement</h3><p className="muted">Every answer carries a deterministic A–D grade for model agreement — never presented as a probability.</p></div>
          <div className="card"><h3>Agriculture</h3><p className="muted">Optional grape-stage guidance where supported.</p></div>
          <div className="card"><h3>Hindi + English</h3><p className="muted">Ask and read in either language.</p></div>
        </div>
      </section>
      <section aria-label="Try a location">
        <h2>Try a location</h2>
        <div className="chips">
          <Link className="chip" href="/chat?loc=Bhopal">Bhopal</Link>
          <Link className="chip" href="/chat?loc=Indore">Indore</Link>
          <Link className="chip" href="/chat?loc=Delhi">Delhi</Link>
          <Link className="chip" href="/chat?loc=Mumbai">Mumbai</Link>
        </div>
      </section>
    </>
  );
}
