import TrendLine from '../charts/TrendLine';
// Real stored snapshots only (one per analysis per day). With fewer than 2 points nothing is drawn,
// because a trend cannot be shown honestly from a single result.

export default function HistoryTrend({ history }) {
  const points = history?.points || [];
  const scored = points.filter((p) => p.score !== null && p.score !== undefined);

  return (
    <div className="card">
      <h2 className="m-0 mb-3 font-display text-lg font-bold">Progress history</h2>
      {!history?.has_enough_history ? (
        <p className="text-sm text-slate-700">Not enough historical data.</p>
      ) : (
        <>
          {scored.length >= 2 && <div className="max-w-2xl"><TrendLine points={scored} /></div>}
          <div className="relative overflow-x-auto"><table className="mt-3 w-full min-w-[520px] text-sm">
            <thead>
              <tr className="border-b border-line text-left text-xs uppercase tracking-wider text-muted">
                <th className="py-1">Date</th><th>Readiness</th><th>Alignment</th><th>High-priority gaps</th><th>Roadmap</th>
              </tr>
            </thead>
            <tbody>
              {points.slice(-10).map((p) => (
                <tr key={p.snapshot_id} className="border-b border-line last:border-0">
                  <td className="py-2">{new Date(`${p.date}T00:00:00`).toLocaleDateString()}</td>
                  <td>{p.score === null || p.score === undefined ? '—' : Math.round(p.score)}</td>
                  <td>{p.alignment_pct === null || p.alignment_pct === undefined ? '—' : `${p.alignment_pct}%`}</td>
                  <td>{p.high_priority_open}</td>
                  <td>{p.roadmap_pct === null || p.roadmap_pct === undefined ? '—' : `${p.roadmap_pct}%`}</td>
                </tr>
              ))}
            </tbody>
          </table></div>
        </>
      )}
    </div>
  );
}
