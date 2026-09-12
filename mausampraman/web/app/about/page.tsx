export default function About() {
  return (
    <>
      <h1>About MausamPraman</h1>
      <p>MausamPraman is location-aware conversational weather intelligence: ask about any place in plain English or Hindi, and get the outlook plus a measured statement of how much to trust it.</p>
      <h2>The problem</h2>
      <p>A bare forecast hides its own uncertainty. When models disagree or a warning is active, a single confident-sounding number can drive a bad call — missed work, a ruined spray round, an unsafe trip.</p>
      <h2>What it does</h2>
      <p>Every answer is built deterministically: resolve the location, fetch weather, check stored warnings, grade forecast trust from measured model disagreement, apply grounded rules where they exist — then phrase the result. The AI chooses words, never verdicts.</p>
      <h2>Why provenance</h2>
      <p>Each answer carries its evidence — coordinates, sources, grade drivers — so anyone can check the answer instead of taking it on faith.</p>
    </>
  );
}
