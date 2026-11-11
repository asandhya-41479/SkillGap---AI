// Career Readiness score + the five components that explain it.
// Every number here comes from the backend; nothing is calculated in React.

const COMPONENTS = [
  ['alignment', 'Skill alignment', 'How closely all your skills match the role (required skills count most).'],
  ['required_coverage', 'Required skills fully covered', 'Share of required skills that are a strong match.'],
  ['evidence', 'Demonstrated evidence', 'Projects or GitHub work that back up your skills.'],
  ['gap_health', 'Freedom from high-priority gaps', '100% means no high-priority gaps remain.'],
  ['roadmap', 'Roadmap progress', 'Roadmap tasks completed. Counts least: learning is not proof.'],
];

const pct = (v) => (v === null || v === undefined ? '—' : `${Math.round(v * 1000) / 10}%`);

function Tile({ label, value, hint }) {
  return (
    <div className="bg-gray-50 rounded p-3">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-xl font-semibold">{value}</div>
      {hint && <div className="text-xs text-gray-400">{hint}</div>}
    </div>
  );
}

export default function ScoreSummary({ snap }) {
  const m = snap.metrics || {};
  const notEnough = snap.score === null;

  return (
    <div className="bg-white border rounded-lg p-4 mb-4">
      <div className="text-xs font-semibold tracking-wide text-gray-500">CAREER READINESS</div>
      {notEnough ? (
        <>
          <div className="text-3xl font-bold my-1">Not enough data</div>
          <p className="text-sm text-gray-600">At least 3 analysed job requirements are needed to calculate a score.</p>
        </>
      ) : (
        <div className="flex items-baseline gap-3 my-1">
          <span className="text-5xl font-bold">{Math.round(snap.score)}</span>
          <span className="text-xl text-gray-500">/ 100</span>
          <span className="ml-2 px-2 py-0.5 rounded bg-purple-100 text-purple-800 text-sm font-medium">{snap.label}</span>
        </div>
      )}
      <p className="text-xs text-gray-500">
        How well your current, evidenced skills match this role. It is not a hiring probability or a guarantee.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
        <Tile label="Skill alignment" value={m.alignment_pct === null || m.alignment_pct === undefined ? '—' : `${m.alignment_pct}%`} />
        <Tile label="Required skills covered" value={`${m.required_covered ?? 0} / ${m.required_total ?? 0}`} hint="strong matches only" />
        <Tile label="Roadmap progress" value={m.roadmap_pct === null || m.roadmap_pct === undefined ? 'No roadmap' : `${m.roadmap_pct}%`} />
        <Tile label="High-priority gaps" value={m.high_priority_open ?? 0} />
      </div>

      {!notEnough && (
        <div className="mt-4 space-y-2">
          <div className="text-sm font-semibold">Why this score</div>
          {COMPONENTS.map(([key, label, help]) => {
            const value = snap.components?.[key];
            const weight = snap.weights?.[key];
            if (value === null || value === undefined) {
              return key === 'roadmap' ? (
                <p key={key} className="text-xs text-gray-500">
                  Roadmap progress is not included because this analysis has no roadmap. The other weights were scaled up.
                </p>
              ) : null;
            }
            return (
              <div key={key} title={help}>
                <div className="flex justify-between text-sm">
                  <span>{label}</span>
                  <span className="text-gray-600">
                    {pct(value)}
                    {weight !== undefined && <span className="text-gray-400"> · weight {Math.round(weight * 100)}%</span>}
                  </span>
                </div>
                <div className="h-2 bg-gray-200 rounded">
                  <div className="h-2 bg-purple-500 rounded" style={{ width: `${Math.min(100, value * 100)}%` }} />
                </div>
              </div>
            );
          })}
          <p className="text-xs text-gray-400">Formula version {snap.formula_version}</p>
        </div>
      )}
    </div>
  );
}
