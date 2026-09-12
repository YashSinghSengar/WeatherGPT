export default function LoadingSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading answer">
      <div className="card"><div className="skel skel-line w90" /><div className="skel skel-line w70" /></div>
      <div className="card"><div className="skel skel-line w40" /></div>
      <div className="card"><div className="skel skel-line w75" /><div className="skel skel-line w60" /><div className="skel skel-line w70" /></div>
    </div>
  );
}
