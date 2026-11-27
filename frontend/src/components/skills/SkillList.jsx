import { useMemo, useState } from 'react';
import { CATEGORY_LABEL } from './SkillForm';
import { symbolOf } from '../../lib/gap';

const FILTERS = [
  { key: 'all', label: 'All skills' },
  { key: 'self', label: 'Self-declared' },
  { key: 'demo', label: 'Demonstrated' },
];

const LEVEL_DOT = { beginner: 'bg-slate-400', intermediate: 'bg-amber-500', advanced: 'bg-green-600' };

// Skills table with filter tabs and a search box (filtering happens in the browser).
export default function SkillList({ profile, onEdit, onDelete }) {
  const [filter, setFilter] = useState('all');
  const [query, setQuery] = useState('');

  const counts = {
    all: profile.length,
    self: profile.filter((s) => s.sources.includes('manual')).length,
    demo: profile.filter((s) => s.demonstrated).length,
  };

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    return profile
      .filter((s) => (filter === 'self' ? s.sources.includes('manual') : filter === 'demo' ? s.demonstrated : true))
      .filter((s) => !q || s.skill_name.toLowerCase().includes(q) || (CATEGORY_LABEL[s.category] || s.category).toLowerCase().includes(q));
  }, [profile, filter, query]);

  return (
    <section className="card flex min-w-0 flex-col gap-4 p-0">
      <div className="flex flex-wrap items-center justify-between gap-3 px-5 pt-5">
        <div role="group" aria-label="Filter skills" className="flex flex-wrap gap-2">
          {FILTERS.map((f) => (
            <button key={f.key} type="button" onClick={() => setFilter(f.key)} aria-pressed={filter === f.key}
              className={`min-h-10 rounded-full px-4 text-sm font-semibold transition ${filter === f.key ? 'bg-ink text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}`}>
              {f.label} ({counts[f.key]})
            </button>
          ))}
        </div>
        <label className="flex h-10 w-full items-center gap-2 rounded-xl border-[1.5px] border-slate-300 px-3 sm:w-64 focus-within:border-brand focus-within:ring-4 focus-within:ring-brand-soft">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#475569" strokeWidth="2" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="M20 20l-4-4" /></svg>
          <span className="sr-only">Search skills</span>
          <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search skills…"
            className="h-full min-w-0 flex-1 border-0 bg-transparent text-sm outline-none placeholder:text-slate-500" />
        </label>
      </div>

      {profile.length === 0 ? (
        <p className="m-0 px-5 pb-6 text-muted">No skills yet. Add one above, or connect GitHub to detect them.</p>
      ) : rows.length === 0 ? (
        <p className="m-0 px-5 pb-6 text-muted">No skills match “{query}”.</p>
      ) : (
        <div className="relative w-full max-w-full overflow-x-auto">
          <table className="w-full min-w-[720px] border-collapse text-sm">
            <thead>
              <tr className="border-y border-line bg-slate-50 text-left text-xs uppercase tracking-wider text-muted">
                <th scope="col" className="px-5 py-3 font-bold">Skill</th>
                <th scope="col" className="px-3 py-3 font-bold">Category</th>
                <th scope="col" className="px-3 py-3 font-bold">Level</th>
                <th scope="col" className="px-3 py-3 font-bold">Source</th>
                <th scope="col" className="px-3 py-3 font-bold">Evidence</th>
                <th scope="col" className="px-5 py-3 text-right font-bold"><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((s) => (
                <tr key={s.skill_name} className="border-b border-line last:border-0 hover:bg-slate-50/60">
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-3">
                      <span className="flex h-9 w-9 flex-none items-center justify-center rounded-lg bg-brand-soft font-display text-sm font-bold text-brand-dark">{symbolOf(s.skill_name)}</span>
                      <span className="font-semibold text-ink">{s.skill_name}</span>
                    </div>
                  </td>
                  <td className="px-3 py-3.5"><span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{CATEGORY_LABEL[s.category] || s.category}</span></td>
                  <td className="px-3 py-3.5">
                    {s.self_assessed_level
                      ? <span className="flex items-center gap-2 capitalize"><span className={`h-2 w-2 rounded-full ${LEVEL_DOT[s.self_assessed_level]}`} />{s.self_assessed_level}</span>
                      : <span className="text-muted">—</span>}
                  </td>
                  <td className="px-3 py-3.5 text-slate-700">{s.sources.map((x) => (x === 'github' ? 'GitHub' : 'Manual')).join(' + ')}</td>
                  <td className="px-3 py-3.5">
                    {s.demonstrated ? (
                      <span className="inline-flex flex-col">
                        <span className="inline-flex items-center gap-1.5 font-semibold text-green-700">
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" aria-hidden="true"><path d="M5 12l5 5 9-10" /></svg>
                          {s.evidence_count} repositor{s.evidence_count === 1 ? 'y' : 'ies'}
                        </span>
                        {s.evidence?.[0]?.repo_name && <span className="max-w-[220px] truncate text-xs text-muted">{s.evidence.map((e) => e.repo_name).join(', ')}</span>}
                      </span>
                    ) : <span className="text-muted">Not yet demonstrated</span>}
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    {s.sources.includes('manual') && (
                      <span className="inline-flex gap-1">
                        <button type="button" onClick={() => onEdit(s)} className="min-h-9 rounded-lg px-3 text-sm font-semibold text-brand hover:bg-brand-soft">Edit</button>
                        <button type="button" onClick={() => onDelete(s)} className="min-h-9 rounded-lg px-3 text-sm font-semibold text-red-700 hover:bg-red-50">Delete</button>
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
