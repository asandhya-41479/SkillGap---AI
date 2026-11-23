import { CLASSIFICATION_TEXT } from './labels';

// Before vs after two real gap analyses of the same job. Alignment changes are shown in
// PERCENTAGE POINTS (62% -> 74% is +12 percentage points, not "+19%").

const signed = (n) => (n > 0 ? `+${n}` : `${n}`);
const round1 = (n) => Math.round(n * 10) / 10;

function Row({ label, before, after, unit = '', deltaUnit = '' }) {
  const both = before !== null && before !== undefined && after !== null && after !== undefined;
  const delta = both ? round1(after - before) : null;
  const color = delta > 0 ? 'text-green-700' : delta < 0 ? 'text-red-700' : 'text-gray-500';
  return (
    <div className="flex justify-between items-baseline py-1 text-sm border-b last:border-0">
      <span className="text-gray-600">{label}</span>
      <span>
        {both ? `${before}${unit} → ${after}${unit}` : '—'}
        {delta !== null && delta !== 0 && deltaUnit && <span className={`ml-2 font-semibold ${color}`}>{signed(delta)} {deltaUnit}</span>}
      </span>
    </div>
  );
}

// For counts of gaps, fewer is better, so the colour is reversed.
function CountRow({ label, before, after, fewerIsBetter = false }) {
  if (before === null || before === undefined) {
    return (
      <div className="flex justify-between items-baseline py-1 text-sm border-b last:border-0">
        <span className="text-gray-600">{label}</span>
        <span>— → {after}</span>
      </div>
    );
  }
  const delta = after - before;
  const good = fewerIsBetter ? delta < 0 : delta > 0;
  return (
    <div className="flex justify-between items-baseline py-1 text-sm border-b last:border-0">
      <span className="text-gray-600">{label}</span>
      <span>
        {before} → {after}
        {delta !== 0 && <span className={`ml-2 font-semibold ${good ? 'text-green-700' : 'text-red-700'}`}>{signed(delta)}</span>}
      </span>
    </div>
  );
}

export default function ComparisonCard({ comparison, scoreBefore, scoreAfter, hasPrevious }) {
  return (
    <div className="bg-white border rounded-lg p-4 mb-4">
      <div className="text-sm font-semibold mb-2">Before vs after</div>
      {!hasPrevious ? (
        <p className="text-sm text-gray-600">
          Only one gap analysis exists for this job. After you make progress, run the skill gap analysis again to see your improvement here.
        </p>
      ) : !comparison ? (
        <p className="text-sm text-gray-600">Comparison is not available right now.</p>
      ) : (
        <>
          <p className="text-xs text-gray-500 mb-2">
            Analysis #{comparison.from_analysis_id} → analysis #{comparison.to_analysis_id}
          </p>
          <Row label="Skill alignment" before={comparison.alignment_before} after={comparison.alignment_after}
            unit="%" deltaUnit="percentage points" />
          {scoreBefore !== null && scoreAfter !== null && (
            <Row label="Career readiness" before={Math.round(scoreBefore)} after={Math.round(scoreAfter)} deltaUnit="points" />
          )}
          {comparison.before_details_unavailable && (
            <p className="text-xs text-gray-500 mb-1">
              The job's requirements were re-extracted after analysis #{comparison.from_analysis_id}, so its
              per-skill details are no longer available. Its alignment score is still shown.
            </p>
          )}
          <CountRow label="Strong matches" before={comparison.strong_before} after={comparison.strong_after} />
          <CountRow label="High-priority gaps" before={comparison.high_priority_before} after={comparison.high_priority_after} fewerIsBetter />
          {comparison.skill_changes?.length > 0 && (
            <div className="mt-3">
              <div className="text-xs font-semibold text-gray-500 mb-1">Skills that changed</div>
              <ul className="text-sm space-y-0.5">
                {comparison.skill_changes.map((c) => (
                  <li key={c.skill_name}>
                    <b>{c.skill_name}</b>: {CLASSIFICATION_TEXT[c.before] || c.before} → {CLASSIFICATION_TEXT[c.after] || c.after}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}
