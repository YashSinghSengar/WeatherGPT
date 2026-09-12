const LABELS: Record<string, string> = { A: "High confidence", B: "Moderate confidence", C: "Low confidence", D: "Insufficient confidence" };

export default function GradeBadge({ grade }: { grade: string }) {
  const label = LABELS[grade] || "Unknown confidence";
  return (
    <span className={`grade-badge grade-${grade}`} role="status" aria-label={`${grade}, ${label}`}>
      <strong>{grade}</strong>
      <span>· {label}</span>
    </span>
  );
}
