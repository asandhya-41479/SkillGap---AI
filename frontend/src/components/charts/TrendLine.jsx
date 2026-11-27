// Small line chart of readiness scores over time (0-100). Needs at least 2 points.
export default function TrendLine({ points }) {
  const pts = points.filter((p) => p.score !== null && p.score !== undefined);
  if (pts.length < 2) {
    return <p className="m-0 rounded-xl bg-slate-50 p-4 text-sm text-muted">Not enough history yet — the trend appears after your second readiness check.</p>;
  }
  const W = 560, H = 200, L = 40, Rr = 20, T = 20, B = 170;
  const x = (i) => L + ((W - L - Rr) * i) / (pts.length - 1);
  const y = (v) => B - ((B - T) * v) / 100;
  const line = pts.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)} ${y(p.score).toFixed(1)}`).join(' ');
  const area = `${line} L${x(pts.length - 1)} ${B} L${x(0)} ${B} Z`;
  const aria = `Readiness over time: ${pts.map((p) => `${p.date} ${Math.round(p.score)}`).join(', ')}`;
  return (
    <svg viewBox={`0 0 ${W} ${H + 20}`} width="100%" role="img" aria-label={aria}>
      {[0, 50, 100].map((v) => (
        <g key={v}>
          <line x1={L} x2={W - Rr} y1={y(v)} y2={y(v)} stroke="#E2E8F0" />
          <text x={L - 8} y={y(v) + 4} textAnchor="end" fontSize="11" fill="#64748B" fontFamily="Inter, sans-serif">{v}</text>
        </g>
      ))}
      <path d={area} fill="#2563EB" fillOpacity="0.1" />
      <path d={line} fill="none" stroke="#2563EB" strokeWidth="3" strokeLinejoin="round" />
      {pts.map((p, i) => (
        <g key={`${p.snapshot_id}-${i}`}>
          <circle cx={x(i)} cy={y(p.score)} r={i === pts.length - 1 ? 6 : 4.5} fill={i === pts.length - 1 ? '#2563EB' : '#FFFFFF'} stroke="#2563EB" strokeWidth="2.5" />
          <text x={x(i)} y={y(p.score) - 12} textAnchor="middle" fontSize="12" fontWeight="700" fill="#0F172A" fontFamily="Inter, sans-serif">{Math.round(p.score)}</text>
          {(i === 0 || i === pts.length - 1 || pts.length <= 6) && (
            <text x={x(i)} y={H + 12} textAnchor="middle" fontSize="11" fill="#64748B" fontFamily="Inter, sans-serif">
              {new Date(p.date).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })}
            </text>
          )}
        </g>
      ))}
    </svg>
  );
}
