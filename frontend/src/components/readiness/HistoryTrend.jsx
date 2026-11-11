// Real stored snapshots only (one per analysis per day). With fewer than 2 points nothing is drawn,
// because a trend cannot be shown honestly from a single result.

function Sparkline({ values }) {
  const W = 320, H = 60, P = 6;
  const step = values.length > 1 ? (W - 2 * P) / (values.length - 1) : 0;
  const y = (v) => H - P - (v / 100) * (H - 2 * P);   // score is 0-100, so the scale is fixed and honest
  const pts = values.map((v, i) => `${P + i * step},${y(v)}`).join(' ');
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-sm h-16" role="img" aria-label="Career readiness over time">
      <line x1={P} x2={W - P} y1={y(50)} y2={y(50)} stroke="#e5e7eb" strokeDasharray="3 3" />
      <polyline points={pts} fill="none" stroke="#7c3aed" strokeWidth="2" />
      {values.map((v, i) => <circle key={i} cx={P + i * step} cy={y(v)} r="3" fill="#7c3aed" />)}
    </svg>
  );
}

export default function HistoryTrend({ history }) {
  const points = history?.points || [];
  const scored = points.filter((p) => p.score !== null && p.score !== undefined);

  return (
    <div className="bg-white border rounded-lg p-4 mb-4">
      <div className="text-sm font-semibold mb-2">Progress history</div>
      {!history?.has_enough_history ? (
        <p className="text-sm text-gray-600">Not enough historical data.</p>
      ) : (
        <>
          {scored.length >= 2 && <Sparkline values={scored.map((p) => p.score)} />}
          <table className="w-full text-sm mt-2">
            <thead>
              <tr className="text-left text-xs text-gray-500">
                <th className="py-1">Date</th><th>Readiness</th><th>Alignment</th><th>High-priority gaps</th><th>Roadmap</th>
              </tr>
            </thead>
            <tbody>
              {points.slice(-10).map((p) => (
                <tr key={p.snapshot_id} className="border-t">
                  <td className="py-1">{new Date(`${p.date}T00:00:00`).toLocaleDateString()}</td>
                  <td>{p.score === null || p.score === undefined ? '—' : Math.round(p.score)}</td>
                  <td>{p.alignment_pct === null || p.alignment_pct === undefined ? '—' : `${p.alignment_pct}%`}</td>
                  <td>{p.high_priority_open}</td>
                  <td>{p.roadmap_pct === null || p.roadmap_pct === undefined ? '—' : `${p.roadmap_pct}%`}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
