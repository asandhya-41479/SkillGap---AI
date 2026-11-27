import Gauge from '../charts/Gauge';

// Career Readiness score + the five components that explain it.
// Every number here comes from the backend; nothing is calculated in React.

const COMPONENTS = [
  ['alignment', 'Skill alignment', 'How closely all your skills match the role (required skills count most).', '#2563EB'],
  ['required_coverage', 'Required skills fully covered', 'Share of required skills that are a strong match.', '#7C3AED'],
  ['evidence', 'Demonstrated evidence', 'Projects or GitHub work that back up your skills.', '#16A34A'],
  ['gap_health', 'Freedom from high-priority gaps', '100% means no high-priority gaps remain.', '#EA580C'],
  ['roadmap', 'Roadmap progress', 'Roadmap tasks completed. Counts least: learning is not proof.', '#0891B2'],
];

const pct = (v) => (v === null || v === undefined ? '—' : `${Math.round(v * 1000) / 10}%`);

function Tile({ label, value, hint, tone = 'text-ink' }) {
  return (
    <div className="rounded-xl bg-slate-50 p-3.5">
      <p className="eyebrow m-0">{label}</p>
      <p className={`m-0 mt-1 font-display text-2xl font-bold ${tone}`}>{value}</p>
      {hint && <p className="m-0 text-xs text-muted">{hint}</p>}
    </div>
  );
}

export default function ScoreSummary({ snap, previousScore = null }) {
  const m = snap.metrics || {};
  const notEnough = snap.score === null;

  return (
    <section className="card grid gap-6 lg:grid-cols-[340px_1fr]">
      <div className="flex flex-col items-center gap-2 text-center">
        <p className="eyebrow m-0 self-start">Career readiness</p>
        {notEnough ? (
          <>
            <p className="m-0 mt-6 font-display text-2xl font-bold">Not enough data</p>
            <p className="m-0 text-sm text-muted">At least 3 analysed job requirements are needed to calculate a score.</p>
          </>
        ) : (
          <>
            <Gauge value={snap.score} previous={previousScore} />
            <span className="rounded-full bg-orange-100 px-3 py-1 text-sm font-bold text-orange-800">{snap.label}</span>
          </>
        )}
        <p className="m-0 mt-1 text-xs text-muted">How well your current, evidenced skills match this role. It is not a hiring probability or a guarantee.</p>
        <div className="mt-2 grid w-full grid-cols-2 gap-2.5 text-left">
          <Tile label="Alignment" value={m.alignment_pct === null || m.alignment_pct === undefined ? '—' : `${m.alignment_pct}%`} tone="text-brand" />
          <Tile label="Required" value={`${m.required_covered ?? 0}/${m.required_total ?? 0}`} hint="strong matches" />
          <Tile label="Roadmap" value={m.roadmap_pct === null || m.roadmap_pct === undefined ? '—' : `${m.roadmap_pct}%`} hint={m.roadmap_pct == null ? 'no roadmap' : undefined} />
          <Tile label="High gaps" value={m.high_priority_open ?? 0} tone="text-high" />
        </div>
      </div>

      {!notEnough && (
        <div className="flex flex-col gap-4">
          <div>
            <h2 className="m-0 font-display text-lg font-bold">Why this score</h2>
            <p className="m-0 mt-1 text-sm text-muted">Five parts, each with a fixed weight. Bars show how much of each part you have.</p>
          </div>
          {COMPONENTS.map(([key, label, help, color]) => {
            const value = snap.components?.[key];
            const weight = snap.weights?.[key];
            if (value === null || value === undefined) {
              return key === 'roadmap' ? (
                <p key={key} className="m-0 rounded-xl bg-slate-50 px-3.5 py-2.5 text-sm text-muted">
                  Roadmap progress is not included because this analysis has no roadmap. The other weights were scaled up.
                </p>
              ) : null;
            }
            return (
              <div key={key}>
                <div className="mb-1.5 flex items-baseline justify-between gap-3 text-sm">
                  <span className="font-semibold text-ink">{label}</span>
                  <span className="text-slate-700">
                    <b>{pct(value)}</b>
                    {weight !== undefined && <span className="ml-2 rounded-md bg-slate-100 px-1.5 py-0.5 text-xs font-semibold text-muted">weight {Math.round(weight * 100)}%</span>}
                  </span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full" style={{ width: `${Math.min(100, value * 100)}%`, background: color }} />
                </div>
                <p className="m-0 mt-1 text-xs text-muted">{help}</p>
              </div>
            );
          })}
          <p className="m-0 text-xs text-muted">Formula version {snap.formula_version}</p>
        </div>
      )}
    </section>
  );
}
