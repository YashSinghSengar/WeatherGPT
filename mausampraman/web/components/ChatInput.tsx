"use client";
import { useState } from "react";

export default function ChatInput({ onAsk, loading }: { onAsk: (q: string, lang: string) => void; loading: boolean }) {
  const [query, setQuery] = useState("");
  const [lang, setLang] = useState("en");
  return (
    <form className="chat-form" onSubmit={(e) => { e.preventDefault(); if (query.trim() && !loading) onAsk(query.trim(), lang); }}>
      <label htmlFor="q" className="muted">Your question</label>
      <input id="q" type="text" value={query} onChange={(e) => setQuery(e.target.value)}
        placeholder="Will it rain tonight in Nashik?" disabled={loading} />
      <label htmlFor="lang" className="muted">Language</label>
      <select id="lang" value={lang} onChange={(e) => setLang(e.target.value)} disabled={loading}>
        <option value="en">English</option>
        <option value="hi">हिंदी</option>
      </select>
      <button className="btn" type="submit" disabled={loading || !query.trim()}>
        {loading ? "Asking…" : "Ask"}
      </button>
    </form>
  );
}
