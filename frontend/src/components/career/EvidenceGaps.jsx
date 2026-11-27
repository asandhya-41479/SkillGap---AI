import { Link } from 'react-router-dom';
import { evidenceLabel, IMPORTANCE_TEXT, STATUS_TEXT } from '../readiness/labels';
import { Chip } from './Chip';

// Skill -> required evidence -> current evidence -> missing -> recommended action.
// "Current" lists only real rows from Modules 2, 5 and 6; nothing is assumed.

const SOURCE_TEXT = { progress_evidence: 'Attached', github_detected: 'GitHub detected', roadmap: 'Roadmap' };
const KIND_TEXT = {
  github_repo: 'repository', project_url: 'project link', language: 'language', topic: 'topic tag',
  completed_item: 'completed item',
};

function Current({ items }) {
  if (!items.length) return <p className="text-sm text-muted">None yet</p>;
  return (
    <ul className="space-y-1">
      {items.map((e, i) => (
        <li key={`${e.kind}-${e.url || i}`} className="flex flex-wrap items-center gap-1 text-sm">
          <span>{SOURCE_TEXT[e.source] || e.source} {KIND_TEXT[e.kind] || e.kind}</span>
          {e.status && STATUS_TEXT[e.status] ? <Chip spec={STATUS_TEXT[e.status]} /> : <Chip spec={evidenceLabel(e.strength)} />}
          {e.url && <span className="text-xs text-slate-500 break-all">{e.url}</span>}
        </li>
      ))}
    </ul>
  );
}

export default function EvidenceGaps({ gaps }) {
  if (!gaps?.length) {
    return (
      <div className="card">
        <div className="text-xs font-semibold tracking-wide text-muted">EVIDENCE GAPS</div>
        <p className="text-sm text-slate-700 mt-1">No evidence gaps for the role's important skills.</p>
      </div>
    );
  }
  return (
    <div className="card">
      <div className="flex items-center mb-2">
        <div className="text-xs font-semibold tracking-wide text-muted">EVIDENCE GAPS</div>
        <Link to="/readiness" className="ml-auto text-xs text-brand hover:underline">Add evidence on Career Readiness →</Link>
      </div>
      <div className="space-y-3">
        {gaps.map((g) => (
          <div key={g.skill_name} className="border rounded p-3">
            <div className="flex items-center gap-2">
              <span className="font-semibold">{g.skill_name}</span>
              <span className="text-xs text-muted">{IMPORTANCE_TEXT[g.importance] || g.importance}</span>
            </div>
            <div className="grid md:grid-cols-3 gap-3 mt-2">
              <div>
                <div className="text-xs font-semibold text-muted">REQUIRED</div>
                <ul className="list-disc ml-4 text-sm">{g.required_evidence.map((r) => <li key={r}>{r}</li>)}</ul>
              </div>
              <div>
                <div className="text-xs font-semibold text-muted">CURRENT</div>
                <Current items={g.current_evidence} />
              </div>
              <div>
                <div className="text-xs font-semibold text-muted">MISSING</div>
                <ul className="list-disc ml-4 text-sm text-red-700">{g.missing_evidence.map((m) => <li key={m}>{m}</li>)}</ul>
              </div>
            </div>
            {g.recommended_action_title && (
              <p className="mt-2 text-sm"><span className="text-muted">Recommended action:</span> {g.recommended_action_title}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
