import { useEffect, useRef, useState } from 'react';
import { addEvidence, deleteEvidence, verifyEvidence } from '../../api/evidence';
import { STATUS_TEXT, errorText } from './labels';

// Attach evidence to a skill. The backend validates every URL, checks GitHub ownership and
// structure, and decides the strength. Evidence never changes a skill level by itself.

const EMPTY = { skill_name: '', kind: 'github_repo', url: '', note: '' };

export default function EvidencePanel({ skills, evidence, onChanged, preset }) {
  const [form, setForm] = useState(EMPTY);
  const [busy, setBusy] = useState(null);       // 'add' | evidence id
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const boxRef = useRef(null);

  // "Add evidence for X" from the next-action card pre-fills the skill and scrolls here.
  useEffect(() => {
    if (!preset?.skill) return;
    setForm((f) => ({ ...f, skill_name: preset.skill }));
    boxRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [preset]);

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const run = async (key, fn, okText) => {
    setBusy(key);
    setError('');
    setInfo('');
    try {
      const res = await fn();
      setInfo(okText(res));
      await onChanged();
    } catch (err) {
      setError(errorText(err, 'That did not work. Please try again.'));
    } finally {
      setBusy(null);
    }
  };

  const handleAdd = () =>
    run('add', async () => {
      const res = await addEvidence({ ...form, note: form.note.trim() || null });
      setForm({ ...EMPTY, kind: form.kind });
      return res;
    }, (res) => res.data.verification_detail || 'Evidence added.');

  const handleVerify = (ev) => run(ev.id, () => verifyEvidence(ev.id), (res) => res.data.verification_detail || 'Checked again.');

  const handleDelete = (ev) => {
    if (!window.confirm(`Remove this evidence for ${ev.skill_name}?`)) return;
    run(ev.id, () => deleteEvidence(ev.id), () => 'Evidence removed.');
  };

  const field = 'rounded-xl border-[1.5px] border-slate-300 px-2.5 py-2 w-full';
  const relevant = evidence.filter((e) => skills.some((s) => s.toLowerCase() === e.skill_name.toLowerCase()));
  const other = evidence.length - relevant.length;

  return (
    <div ref={boxRef} className="card">
      <div className="text-sm font-semibold">Skill evidence</div>
      <p className="text-xs text-muted mb-3">
        Completing a roadmap task counts as learning. A verified GitHub repository counts as demonstrated work.
        Evidence never raises your skill level by itself.
      </p>

      {relevant.length === 0 ? (
        <p className="text-sm text-slate-700 mb-3">No evidence attached for this role's skills yet.</p>
      ) : (
        <div className="mb-3">
          {relevant.map((ev) => {
            const st = STATUS_TEXT[ev.verification_status] || { text: ev.verification_status, cls: 'bg-gray-100' };
            return (
              <div key={ev.id} className="border rounded p-2 mb-2 text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <strong>{ev.skill_name}</strong>
                  <span className="text-muted">{ev.kind === 'github_repo' ? 'GitHub' : 'Project link'}</span>
                  <span className={`text-xs px-2 py-0.5 rounded ${st.cls}`}>{st.text}</span>
                  {ev.strength !== null && ev.strength !== undefined && (
                    <span className="text-xs text-muted">strength {ev.strength.toFixed(2)}</span>
                  )}
                  <span className="ml-auto flex gap-3">
                    {ev.kind === 'github_repo' && (
                      <button onClick={() => handleVerify(ev)} disabled={busy !== null}
                        className="text-xs text-brand hover:underline disabled:opacity-50">
                        {busy === ev.id ? 'Checking…' : 'Check again'}
                      </button>
                    )}
                    <button onClick={() => handleDelete(ev)} disabled={busy !== null}
                      className="text-xs text-red-600 hover:underline disabled:opacity-50">Remove</button>
                  </span>
                </div>
                <a href={ev.url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-700 break-all hover:underline">
                  {ev.repo_full_name || ev.url}
                </a>
                {ev.note && <p className="text-xs text-slate-700">{ev.note}</p>}
              </div>
            );
          })}
        </div>
      )}
      {other > 0 && <p className="text-xs text-slate-500 mb-3">{other} more item(s) belong to skills outside this role.</p>}

      <div className="grid grid-cols-2 gap-3 text-sm">
        <label>Skill
          <select value={form.skill_name} onChange={set('skill_name')} className={field}>
            <option value="">Select a skill…</option>
            {skills.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
        <label>Type
          <select value={form.kind} onChange={set('kind')} className={field}>
            <option value="github_repo">My GitHub repository</option>
            <option value="project_url">Project link (live demo)</option>
          </select>
        </label>
        <label className="col-span-2">Link
          <input value={form.url} onChange={set('url')} className={field}
            placeholder={form.kind === 'github_repo' ? 'https://github.com/<you>/<repo>' : 'https://your-project.example.com'} />
        </label>
        <label className="col-span-2">Note (optional)
          <input value={form.note} onChange={set('note')} maxLength={300} className={field} placeholder="What did you build?" />
        </label>
        <button onClick={handleAdd} disabled={!form.skill_name || form.url.trim().length < 12 || busy !== null}
          className="col-span-2 bg-brand text-white px-4 py-2 rounded hover:bg-brand-dark disabled:opacity-50">
          {busy === 'add' ? (form.kind === 'github_repo' ? 'Checking the repository…' : 'Saving…') : 'Add evidence'}
        </button>
      </div>
      {info && <p className="mt-2 text-sm text-green-700">{info}</p>}
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}
