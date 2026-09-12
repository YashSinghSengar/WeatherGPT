export default function About() {
  return (
    <>
      <h1>About MausamPraman</h1>
      <p>MausamPraman is a weather-intelligence prototype built for Smart India Hackathon 2026. It answers Indian weather questions — with a trust grade attached to every answer.</p>
      <h2>The problem</h2>
      <p>Conventional weather answers give a single number with no sense of reliability. When models disagree, or a warning is active, a plain forecast can mislead a farmer into a costly decision.</p>
      <h2>Our approach</h2>
      <p>Measure how much three global forecast models disagree, convert that disagreement into a deterministic A–D confidence grade, let active warnings override everything, match fixed grape-stage advisory rules — and only then let AI phrase the result in English or Hindi.</p>
    </>
  );
}
