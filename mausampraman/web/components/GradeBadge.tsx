const LABELS: Record<string, string> = { A: "High agreement", B: "Moderate agreement", C: "Low agreement", D: "Insufficient agreement" };

export default function GradeBadge({ grade }: { grade: string }) {
  const label = LABELS[grade] || "Unknown agreement";
  return (
    <span className={`grade-badge grade-${grade}`} role="status" aria-label={`${grade}, ${label}`}>
      <strong>{grade}</strong>
      <span>· {label}</span>
    </span>
  );
}
