import { useState } from 'react';
import { PREP_KIND, PRIORITY } from './labels';
import { Chip } from './Chip';
import { errorText } from '../readiness/labels';

// Focused preparation: the role's real gaps, role fundamentals, and the user's own SkillGap AI build.
// Project answer points are curated from the real implementation (never generated).

function Item({ item, onToggle }) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const prepared = item.status === 'PREPARED';

  const toggle = async () => {
    setBusy(true);
    setError('');
    try {
      await onToggle(item.id, prepared ? 'NOT_STARTED' : 'PREPARED');
    } catch (err) {
      setError(errorText(err, 'Could not update this topic.'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className={`border rounded p-3 ${prepared ? 'bg-green-50' : 'bg-white'}`}>
      <div className="flex items-start gap-2">
        <button onClick={() => setOpen(!open)} className="flex-1 text-left">
          <div className="font-medium">{item.topic}</div>
          <div className="flex gap-1 mt-1"><Chip spec={PRIORITY[item.priority]} /></div>
        </button>
        <label className="flex items-center gap-1 text-sm whitespace-nowrap">
          <input type="checkbox" checked={prepared} disabled={busy} onChange={toggle} /> Prepared
        </label>
      </div>
      {open && (
        <div className="mt-2 text-sm">
          <p className="text-slate-700">{item.why}</p>
          <ol className="list-decimal ml-5 mt-2 space-y-2">
            {item.questions.map((q) => (
              <li key={q.question}>
                {q.question}
                {q.answer_points?.length > 0 && (
                  <details className="mt-1">
                    <summary className="text-xs text-brand cursor-pointer">How SkillGap AI actually does it</summary>
                    <ul className="list-disc ml-5 text-gray-700">{q.answer_points.map((a) => <li key={a}>{a}</li>)}</ul>
                  </details>
                )}
              </li>
            ))}
          </ol>
          {item.questions.some((q) => q.source === 'gemini') && (
            <p className="text-xs text-slate-500 mt-1">Questions worded by AI for these topics, then checked by the backend.</p>
          )}
        </div>
      )}
      {error && <p className="text-sm text-red-600 mt-1">{error}</p>}
    </div>
  );
}

export default function InterviewPrep({ prep, onToggle, onRefresh, refreshing }) {
  const [tab, setTab] = useState('GAP');
  if (!prep) return null;
  const items = prep.items.filter((i) => i.kind === tab);

  return (
    <div className="card">
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <div className="text-xs font-semibold tracking-wide text-muted">INTERVIEW PREPARATION</div>
        <span className="text-xs text-slate-700">
          High-priority topics prepared: {prep.high_priority_prepared} / {prep.high_priority_total}
        </span>
        {prep.stale && (
          <button onClick={onRefresh} disabled={refreshing}
            className="ml-auto text-xs bg-brand text-white px-2 py-1 rounded disabled:opacity-50">
            {refreshing ? 'Updating…' : 'Priorities changed: update topics'}
          </button>
        )}
      </div>
      <div className="flex gap-1 border-b mb-3">
        {Object.entries(PREP_KIND).map(([k, label]) => (
          <button key={k} onClick={() => setTab(k)}
            className={`px-3 py-1 text-sm -mb-px border-b-2 ${tab === k ? 'border-brand text-brand' : 'border-transparent text-muted'}`}>
            {label} ({prep.items.filter((i) => i.kind === k).length})
          </button>
        ))}
      </div>
      <div className="space-y-2">
        {items.length ? items.map((i) => <Item key={i.id} item={i} onToggle={onToggle} />)
          : <p className="text-sm text-muted">No topics in this group.</p>}
      </div>
      <p className="text-xs text-slate-500 mt-3">{prep.note}</p>
    </div>
  );
}
