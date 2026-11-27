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
    <div className="card flex flex-col gap-1 bg-navy text-white">
      <span className="self-start rounded-full bg-orange-500 px-3 py-1 text-xs font-bold text-ink">Next best action</span>
      <div className="mt-2 font-display text-xl font-bold leading-snug">{action.title}</div>
      {reasons.length > 0 && (
        <ul className="mt-1 text-sm text-blue-100 list-disc ml-5">
          {reasons.map((r) => <li key={r}>{r}</li>)}
        </ul>
      )}

      <div className="mt-3">
        {action.kind === 'roadmap_item' && action.item_id && (
          <Link to="/roadmap" className="btn-primary bg-white text-ink hover:bg-blue-50">
            Open roadmap
          </Link>
        )}
        {action.kind === 'add_evidence' && (
          <button onClick={() => onAddEvidence(action.skill_name)}
            className="btn-primary bg-white text-ink hover:bg-blue-50">
            Add evidence for {action.skill_name}
          </button>
        )}
        {action.kind === 'rerun_analysis' && (
          <Link to="/skill-gap" className="btn-primary bg-white text-ink hover:bg-blue-50">
            Re-run skill gap analysis
          </Link>
        )}
      </div>

      {action.alternatives?.length > 0 && (
        <p className="mt-2 text-xs text-blue-200">Also possible: {action.alternatives.join(' · ')}</p>
      )}
      {feedback && <p className="mt-3 border-t border-white/15 pt-3 text-sm text-blue-100">{feedback}</p>}
    </div>
  );
}
