import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  deleteOpportunityMatch, getOpportunitySourceStatus, getSavedJobMatches, listOpportunityMatches, matchOpportunity,
} from '../../api/career';
import { errorText } from '../readiness/labels';
import { Chip } from './Chip';

// Real data only: your saved Module 3 jobs, or a real description you paste. The backend finds the
// skills in code and scores them with Module 4's formula; job text is never sent to Gemini.

const GROUPS = [
  ['strong', 'Strong', 'bg-green-100 text-green-800'],
  ['partial', 'Partial', 'bg-amber-100 text-amber-800'],
  ['transferable', 'Transferable', 'bg-sky-100 text-sky-800'],
  ['missing', 'Missing', 'bg-red-100 text-red-800'],
];

function MatchCard({ m, onDelete }) {
  const bd = m.breakdown || {};
  return (
    <div className="border rounded p-3">
      <div className="flex items-start gap-2">
        <div className="flex-1">
          <div className="font-semibold">{m.title || m.target_role || 'Job description'}</div>
          {m.company && <div className="text-xs text-gray-500">{m.company} (entered by you)</div>}
        </div>
        {m.coverage_pct !== null && m.coverage_pct !== undefined && (
          <div className="text-right">
            <div className="text-xl font-bold">{Math.round(m.coverage_pct)}%</div>
            <div className="text-xs text-gray-500">requirement match</div>
          </div>
        )}
        {onDelete && <button onClick={() => onDelete(m.id)} className="text-xs text-red-600 ml-2">Delete</button>}
      </div>
      {m.needs_analysis ? (
        <p className="text-sm text-gray-600 mt-2">
          {m.summary} <Link to="/skill-gap" className="text-purple-700 underline">Run analysis</Link>
        </p>
      ) : (
        <>
          <div className="h-2 bg-gray-100 rounded mt-2">
            <div className="h-2 bg-purple-500 rounded" style={{ width: `${Math.min(100, m.coverage_pct || 0)}%` }} />
          </div>
          <p className="text-sm text-gray-700 mt-2">{m.summary}</p>
          <div className="mt-2 space-y-1">
            {GROUPS.filter(([k]) => bd[k]?.length).map(([k, label, cls]) => (
              <div key={k} className="flex flex-wrap items-center gap-1 text-sm">
                <span className="text-xs text-gray-500 w-24">{label}</span>
                {bd[k].map((s) => <Chip key={s} spec={{ cls }}>{s}</Chip>)}
              </div>
            ))}
          </div>
          {bd.critical?.length > 0 && (
            <p className="text-sm text-red-700 mt-2">Critical gaps (required, missing): {bd.critical.join(', ')}</p>
          )}
          {bd.recommended_action_keys?.length > 0 && (
            <p className="text-xs text-gray-500 mt-1">Your career plan already has actions for these gaps.</p>
          )}
          {m.note && <p className="text-xs text-gray-400 mt-2">{m.note}</p>}
          <p className="text-xs text-gray-400">{m.disclaimer}</p>
        </>
      )}
    </div>
  );
}

export default function OpportunityMatcher() {
  const [status, setStatus] = useState(null);
  const [saved, setSaved] = useState([]);
  const [history, setHistory] = useState([]);
  const [form, setForm] = useState({ job_description: '', title: '', company: '', source_url: '' });
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    const [s, j, h] = await Promise.allSettled([getOpportunitySourceStatus(), getSavedJobMatches(), listOpportunityMatches()]);
    if (s.status === 'fulfilled') setStatus(s.value.data);
    if (j.status === 'fulfilled') setSaved(j.value.data);
    if (h.status === 'fulfilled') setHistory(h.value.data);
    if (j.status === 'rejected') setError('Could not load your saved jobs.');
  }, []);

  useEffect(() => { load(); }, [load]);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      const body = { job_description: form.job_description };
      for (const k of ['title', 'company', 'source_url']) if (form[k].trim()) body[k] = form[k].trim();
      const r = await matchOpportunity(body);
      setResult(r.data);
      await load();
    } catch (err) {
      setError(errorText(err, 'Could not compare this description.'));
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id) => {
    try {
      await deleteOpportunityMatch(id);
      if (result?.id === id) setResult(null);
      await load();
    } catch (err) {
      setError(errorText(err, 'Could not delete this comparison.'));
    }
  };

  const len = form.job_description.length;
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <div className="bg-white border rounded-lg p-4 mb-4">
      <div className="text-xs font-semibold tracking-wide text-gray-500">OPPORTUNITY MATCHING</div>
      {status?.message && (
        <p className="text-sm text-gray-600 bg-gray-50 border rounded p-2 mt-2">{status.message}</p>
      )}

      <h3 className="font-semibold mt-3 mb-2">Your saved jobs</h3>
      {saved.length ? (
        <div className="space-y-2">{saved.map((m) => <MatchCard key={m.job_description_id} m={m} />)}</div>
      ) : (
        <p className="text-sm text-gray-500">
          No saved jobs yet. <Link to="/jobs" className="text-purple-700 underline">Add a job description</Link>.
        </p>
      )}

      <h3 className="font-semibold mt-4 mb-2">Compare a real job description</h3>
      <form onSubmit={submit} className="space-y-2">
        <textarea value={form.job_description} onChange={set('job_description')} rows={6} maxLength={15000}
          placeholder="Paste a job description you found (50 to 15,000 characters)"
          className="w-full border rounded px-2 py-1 text-sm" />
        <div className="grid md:grid-cols-3 gap-2">
          <input value={form.title} onChange={set('title')} maxLength={200} placeholder="Job title (optional)"
            className="border rounded px-2 py-1 text-sm" />
          <input value={form.company} onChange={set('company')} maxLength={200} placeholder="Company (optional)"
            className="border rounded px-2 py-1 text-sm" />
          <input value={form.source_url} onChange={set('source_url')} maxLength={500} placeholder="https:// link (optional)"
            className="border rounded px-2 py-1 text-sm" />
        </div>
        <div className="flex items-center gap-2">
          <button disabled={busy || len < 50}
            className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 disabled:opacity-50 text-sm">
            {busy ? 'Comparing…' : 'Compare with my profile'}
          </button>
          <span className="text-xs text-gray-400">{len} / 15000</span>
        </div>
      </form>
      {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
      {result && <div className="mt-3"><MatchCard m={result} /></div>}

      {history.length > 0 && (
        <details className="mt-4">
          <summary className="text-sm text-purple-700 cursor-pointer">Previous comparisons ({history.length})</summary>
          <div className="space-y-2 mt-2">{history.map((m) => <MatchCard key={m.id} m={m} onDelete={remove} />)}</div>
        </details>
      )}
    </div>
  );
}
