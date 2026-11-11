import { Link } from 'react-router-dom';

// The backend chooses the action deterministically (in-progress task → next unblocked task →
// missing evidence → re-run analysis). Gemini may only reword the summary below it.

const REASON_TEXT = {
  in_progress: 'You already started this task',
  next_scheduled: 'Next task in your learning order',
  prerequisites_met: 'Its prerequisites are done',
  priority_high: 'High-priority skill for this role',
  priority_medium: 'Medium-priority skill',
  priority_low: 'Low-priority skill',
  high_priority_gap: 'High-priority skill still open',
  needs_evidence: 'No solid project or GitHub evidence yet',
  importance_required: 'Required by the role',
  importance_preferred: 'Preferred by the role',
  reanalysis_recommended: 'Your evidence is newer than your gap analysis',
  all_skills_covered: 'All requirements are strong matches',
};

export default function NextActionCard({ action, feedback, onAddEvidence }) {
  if (!action) return null;
  const reasons = (action.reason_codes || []).map((c) => REASON_TEXT[c]).filter(Boolean);

  return (
    <div className="bg-white border-2 border-purple-200 rounded-lg p-4 mb-4">
      <div className="text-xs font-semibold tracking-wide text-purple-700">NEXT BEST ACTION</div>
      <div className="text-lg font-semibold mt-1">{action.title}</div>
      {reasons.length > 0 && (
        <ul className="mt-1 text-sm text-gray-600 list-disc ml-5">
          {reasons.map((r) => <li key={r}>{r}</li>)}
        </ul>
      )}

      <div className="mt-3">
        {action.kind === 'roadmap_item' && action.item_id && (
          <Link to="/roadmap" className="inline-block bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 text-sm">
            Open roadmap
          </Link>
        )}
        {action.kind === 'add_evidence' && (
          <button onClick={() => onAddEvidence(action.skill_name)}
            className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 text-sm">
            Add evidence for {action.skill_name}
          </button>
        )}
        {action.kind === 'rerun_analysis' && (
          <Link to="/skill-gap" className="inline-block bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 text-sm">
            Re-run skill gap analysis
          </Link>
        )}
      </div>

      {action.alternatives?.length > 0 && (
        <p className="mt-2 text-xs text-gray-500">Also possible: {action.alternatives.join(' · ')}</p>
      )}
      {feedback && <p className="mt-3 text-sm text-gray-700 border-t pt-3">{feedback}</p>}
    </div>
  );
}
