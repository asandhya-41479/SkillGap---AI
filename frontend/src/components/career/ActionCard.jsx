import { useState } from 'react';
import { ACTION_STATUS, CATEGORY, PRIORITY } from './labels';
import { Chip } from './Chip';
import { errorText } from '../readiness/labels';

// One career action. WHAT (title), WHY (deterministic reason, optionally reworded by Gemini),
// WHAT EVIDENCE (required list). The user may only change status and evidence; completing an
// action never marks a skill as mastered: Module 6 recalculates readiness from evidence.

export default function ActionCard({ action, rank, onUpdate }) {
  const [open, setOpen] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [url, setUrl] = useState(action.evidence_url || '');
  const [note, setNote] = useState(action.evidence_note || '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const save = async (data) => {
    setSaving(true);
    setError('');
    try {
      await onUpdate(action.id, data);
      setCompleting(false);
    } catch (err) {
      setError(errorText(err, 'Could not update this action.'));
    } finally {
      setSaving(false);
    }
  };

  const onStatus = (value) => {
    if (value === 'COMPLETED') setCompleting(true);
    else save({ status: value });
  };

  const done = action.status === 'COMPLETED' || action.status === 'SKIPPED';

  return (
    <div className={`border rounded-lg p-3 ${done ? 'bg-gray-50' : 'bg-white'}`}>
      <div className="flex flex-wrap items-start gap-2">
        {rank && <span className="text-sm font-bold text-purple-700 w-5">{rank}.</span>}
        <div className="flex-1 min-w-[12rem]">
          <div className={`font-medium ${done ? 'text-gray-500 line-through' : ''}`}>{action.title}</div>
          <div className="flex flex-wrap gap-1 mt-1">
            <Chip spec={PRIORITY[action.priority]} />
            <Chip spec={CATEGORY[action.category]} />
            {action.skill_name && <Chip>{action.skill_name}</Chip>}
          </div>
        </div>
        <select value={action.status} disabled={saving} onChange={(e) => onStatus(e.target.value)}
          className="border rounded px-2 py-1 text-sm">
          {ACTION_STATUS.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
        </select>
      </div>

      <button onClick={() => setOpen(!open)} className="mt-2 text-xs text-purple-700 hover:underline">
        {open ? 'Hide' : 'Why this action?'}
      </button>
      {open && (
        <div className="mt-2 text-sm text-gray-700 space-y-2">
          <p>{action.reason}</p>
          {action.explanation && (
            <p className="text-gray-600 border-l-2 border-purple-200 pl-2">
              {action.explanation} <span className="text-xs text-gray-400">(AI-worded from the reason above)</span>
            </p>
          )}
          {action.evidence_required?.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-gray-500">EVIDENCE TO PRODUCE</div>
              <ul className="list-disc ml-5">{action.evidence_required.map((e) => <li key={e}>{e}</li>)}</ul>
            </div>
          )}
        </div>
      )}

      {completing && (
        <div className="mt-3 border-t pt-3 space-y-2">
          <p className="text-xs text-gray-500">
            Optional: add a link to what you produced. Completing an action does not mark the skill as mastered;
            your readiness updates from the evidence.
          </p>
          <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://github.com/you/project"
            className="w-full border rounded px-2 py-1 text-sm" />
          <input value={note} onChange={(e) => setNote(e.target.value)} maxLength={300} placeholder="Short note (optional)"
            className="w-full border rounded px-2 py-1 text-sm" />
          <div className="flex gap-2">
            <button disabled={saving}
              onClick={() => save({ status: 'COMPLETED', ...(url.trim() && { evidence_url: url.trim() }),
                ...(note.trim() && { evidence_note: note.trim() }) })}
              className="bg-purple-600 text-white px-3 py-1 rounded text-sm hover:bg-purple-700 disabled:opacity-50">
              {saving ? 'Saving…' : 'Mark completed'}
            </button>
            <button onClick={() => setCompleting(false)} className="text-sm text-gray-600 px-2">Cancel</button>
          </div>
        </div>
      )}
      {action.status === 'COMPLETED' && action.evidence_url && !completing && (
        <p className="mt-2 text-xs text-gray-500 break-all">Evidence: {action.evidence_url}</p>
      )}
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}
