"use client";
import { useState } from "react";
import { askBackend, type AskResponse } from "../../lib/api";
import ChatInput from "../../components/ChatInput";
import EmptyState from "../../components/EmptyState";
import ErrorCard from "../../components/ErrorCard";
import LoadingSkeleton from "../../components/LoadingSkeleton";
import GradeBadge from "../../components/GradeBadge";
import PramanCard from "../../components/PramanCard";
import AdvisoryCard from "../../components/AdvisoryCard";
import WarningCard from "../../components/WarningCard";

export default function Chat() {
  const [data, setData] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [last, setLast] = useState<[string, string]>(["", "en"]);

  async function run(q: string, lang: string) {
    setLoading(true); setError(""); setData(null); setLast([q, lang]);
    try {
      setData(await askBackend(q, lang));
    } catch {
      setError("Unable to reach MausamPraman right now. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <h1>Ask MausamPraman</h1>
      <p className="muted">Weather outlooks, grape advisories, warnings, and trust grades — in English or Hindi.</p>
      <ChatInput onAsk={run} loading={loading} />
      {loading && <LoadingSkeleton />}
      {error && !loading && <ErrorCard message={error} onRetry={() => run(last[0], last[1])} />}
      {!loading && !error && !data && <EmptyState onPick={run} />}
      {!loading && !error && data && (
        <>
          <WarningCard data={data} />
          <section className="card" aria-label="Answer">
            <p className="answer-text">{data.answer}</p>
            <GradeBadge grade={data.confidence.grade} />
          </section>
          <AdvisoryCard data={data} />
          <PramanCard data={data} />
        </>
      )}
    </>
  );
}
