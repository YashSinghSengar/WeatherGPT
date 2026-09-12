"use client";
export default function ErrorCard({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="card error-card" role="alert">
      <h3>Something went wrong</h3>
      <p>{message}</p>
      <button className="btn" onClick={onRetry}>Retry</button>
    </div>
  );
}
