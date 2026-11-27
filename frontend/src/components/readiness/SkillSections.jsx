import { CLASSIFICATION_TEXT, IMPORTANCE_TEXT, evidenceLabel } from './labels';

// High-priority gap alerts, strong matches and remaining gaps, built from the backend's per-skill breakdown.
// The "recommended action" only points at data that exists (a real roadmap task or real evidence).

const IMPORTANCE_RANK = { required: 0, preferred: 1, optional: 2 };
const PRIORITY_RANK = { high: 0, medium: 1, low: 2, none: 3 };
const bySeverity = (a, b) =>
  (PRIORITY_RANK[a.priority] ?? 3) - (PRIORITY_RANK[b.priority] ?? 3) ||
  (IMPORTANCE_RANK[a.importance] ?? 3) - (IMPORTANCE_RANK[b.importance] ?? 3) ||
  a.skill_name.localeCompare(b.skill_name);

function weeksText(item) {
  if (!item?.is_scheduled || !item.start_week) return '';
  return item.start_week === item.end_week ? ` (week ${item.start_week})` : ` (weeks ${item.start_week}–${item.end_week})`;
}

function recommendedAction(skill, item) {
  if (skill.evidence_strength >= 0.6) return 'Evidence added. Re-run the skill gap analysis so the match can be updated.';
  if (item && item.status !== 'completed' && item.status !== 'skipped') {
    return `${item.status === 'in_progress' ? 'Finish' : 'Complete'} the ${skill.skill_name} roadmap task${weeksText(item)}.`;
  }
  if (item && item.status === 'completed') return 'Learning done. Attach a project or GitHub repository as evidence.';
  return 'Attach project or GitHub evidence, or update your roadmap to include it.';
}

function Badge({ cls, children }) {
  return <span className={`text-xs px-2 py-0.5 rounded ${cls}`}>{children}</span>;
}

export default function SkillSections({ breakdown, roadmapItems }) {
  if (!breakdown?.length) return null;
  const itemFor = (name) => roadmapItems[name.toLowerCase()];

  const high = breakdown.filter((s) => s.priority === 'high').sort(bySeverity);
  const strong = breakdown.filter((s) => s.classification === 'strong').sort(bySeverity);
  const remaining = breakdown.filter((s) => s.classification !== 'strong' && s.priority !== 'high').sort(bySeverity);

  return (
    <>
      <div className="card">
        <h2 className="m-0 mb-3 font-display text-lg font-bold">High-priority gaps ({high.length})</h2>
        {high.length === 0 ? (
          <p className="text-sm text-slate-700">No high-priority gaps remain for this role.</p>
        ) : (
          high.map((s) => {
            const ev = evidenceLabel(s.evidence_strength);
            return (
              <div key={s.skill_name} className="mb-2.5 rounded-xl bg-orange-50 p-3.5 ring-1 ring-orange-200">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-high px-2 py-0.5 text-xs font-bold text-white">High priority</span>
                  <strong>{s.skill_name}</strong>
                  <Badge cls="bg-white text-gray-700">{IMPORTANCE_TEXT[s.importance] || s.importance} by target role</Badge>
                  <Badge cls="bg-white text-gray-700">Current status: {CLASSIFICATION_TEXT[s.classification] || s.classification}</Badge>
                  <Badge cls={ev.cls}>{ev.text}</Badge>
                </div>
                <p className="text-sm mt-1"><b>Recommended action:</b> {recommendedAction(s, itemFor(s.skill_name))}</p>
              </div>
            );
          })
        )}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="card">
          <h2 className="m-0 mb-3 font-display text-lg font-bold">Strong matches ({strong.length})</h2>
          {strong.length === 0 && <p className="text-sm text-slate-700">None yet.</p>}
          {strong.map((s) => {
            const ev = evidenceLabel(s.evidence_strength);
            return (
              <div key={s.skill_name} className="flex items-center justify-between gap-2 border-b border-line py-2 text-sm last:border-0">
                <span>{s.skill_name} <span className="text-slate-500">· {IMPORTANCE_TEXT[s.importance] || s.importance}</span></span>
                <Badge cls={ev.cls}>{ev.text}</Badge>
              </div>
            );
          })}
        </div>
        <div className="card">
          <h2 className="m-0 mb-3 font-display text-lg font-bold">Other remaining gaps ({remaining.length})</h2>
          {remaining.length === 0 && <p className="text-sm text-slate-700">None.</p>}
          {remaining.map((s) => (
            <div key={s.skill_name} className="flex items-center justify-between gap-2 border-b border-line py-2 text-sm last:border-0">
              <span>{s.skill_name} <span className="text-slate-500">· {IMPORTANCE_TEXT[s.importance] || s.importance}</span></span>
              <span className="text-slate-700">{CLASSIFICATION_TEXT[s.classification] || s.classification} · {s.priority} priority</span>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
