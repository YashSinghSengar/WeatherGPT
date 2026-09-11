"use client";
import { useState } from "react";

export default function Page() {
  const [query, setQuery] = useState("Nashik weather");
  const [lang, setLang] = useState("en");
  const [out, setOut] = useState("");

  async function submit() {
    const base = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
    const r = await fetch(`${base}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, lang, crop: "grape" }),
    });
    setOut(await r.text());
  }

  return (
    <main style={{ padding: 24, fontFamily: "sans-serif" }}>
      <h1>MausamPraman</h1>
      <input value={query} onChange={(e) => setQuery(e.target.value)} style={{ width: 300 }} />
      <select value={lang} onChange={(e) => setLang(e.target.value)}>
        <option value="en">English</option>
        <option value="hi">Hindi</option>
      </select>
      <button onClick={submit}>Ask</button>
      <pre>{out}</pre>
    </main>
  );
}
