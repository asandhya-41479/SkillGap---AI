import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { listAnalyses } from '../api/skillGap';
import { createRoadmap, regenerateRoadmap, improveRoadmap, listRoadmaps, getRoadmap, setItemStatus, deleteRoadmap } from '../api/roadmaps';
import RoadmapItemCard from '../components/roadmap/RoadmapItemCard';

const errorText = (err, fallback) =>
  typeof err.response?.data?.detail === 'string' ? err.response.data.detail : fallback;

export default function Roadmap() {
  const [analyses, setAnalyses] = useState([]);
  const [roadmaps, setRoadmaps] = useState([]);
  const [roadmap, setRoadmap] = useState(null);
  const [form, setForm] = useState({
    analysis_id: '', hours_per_week: 8, duration_weeks: 8, experience_level: 'intermediate', learning_style: 'balanced',
  });
  const [creating, setCreating] = useState(false);
  const [upd, setUpd] = useState({ mode: 'adapt', hours: '', weeks: '' });
  const [updating, setUpdating] = useState(false);
  const [improving, setImproving] = useState(false);
  const [busyItem, setBusyItem] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([listAnalyses(), listRoadmaps()])
      .then(([a, r]) => {
        setAnalyses(a.data.filter((x) => x.status === 'completed'));
        setRoadmaps(r.data);
        if (r.data.length) return getRoadmap(r.data[0].id).then((d) => setRoadmap(d.data));
      })
      .catch(() => setError('Could not load your roadmaps.'));
  }, []);


  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const open = async (id) => {
    setError('');
    try { setRoadmap((await getRoadmap(id)).data); } catch { setError('Could not open that roadmap.'); }
  };

  const handleCreate = async () => {
    if (!form.analysis_id) return;
    setCreating(true);
    setError('');
    try {
      const { data } = await createRoadmap({
        ...form,
        analysis_id: Number(form.analysis_id),
        hours_per_week: Number(form.hours_per_week),
        duration_weeks: Number(form.duration_weeks),
      });
      setRoadmap(data);
      setRoadmaps([data, ...roadmaps]);
    } catch (err) {
      setError(errorText(err, 'Could not create the roadmap. Check the hours and weeks and try again.'));
    } finally {
      setCreating(false);
    }
  };

  const handleUpdate = async () => {
    setUpdating(true);
    setError('');
    try {

      const body = { mode: upd.mode };
      if (upd.hours) body.hours_per_week = Number(upd.hours);
      if (upd.weeks) body.duration_weeks = Number(upd.weeks);
      const { data } = await regenerateRoadmap(roadmap.id, body);
      setRoadmap(data);
      setRoadmaps([data, ...roadmaps.map((r) => (r.id === roadmap.id ? { ...r, lifecycle: 'superseded' } : r))]);
    } catch (err) {
      setError(errorText(err, 'Could not update the roadmap. Please try again.'));
    } finally {
      setUpdating(false);
    }
  };

  const handleImprove = async () => {
    setImproving(true);
    setError('');
    try {
      const { data } = await improveRoadmap(roadmap.id);
      setRoadmap(data);
      setRoadmaps(roadmaps.map((r) => (r.id === data.id ? { ...r, generation_source: data.generation_source } : r)));
    } catch (err) {
      setError(errorText(err, 'Could not improve the wording. Please try again later.'));
    } finally {
      setImproving(false);
    }
  };

  const handleStatus = async (item, status) => {
    setBusyItem(item.id);
    setError('');
    try {
      await setItemStatus(roadmap.id, item.id, status);

      setRoadmap((await getRoadmap(roadmap.id)).data);
    } catch (err) {
      setError(errorText(err, 'Could not update that task.'));
    } finally {
      setBusyItem(null);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Delete this roadmap and its progress?')) return;
    try {
      await deleteRoadmap(roadmap.id);
      const rest = roadmaps.filter((r) => r.id !== roadmap.id);
      setRoadmaps(rest);
      setRoadmap(null);
      if (rest.length) open(rest[0].id);
    } catch {
      setError('Could not delete the roadmap.');
    }
  };

  const scheduled = roadmap?.items.filter((i) => i.is_scheduled) ?? [];
  const deferred = roadmap?.items.filter((i) => !i.is_scheduled) ?? [];
  const p = roadmap?.progress;
  const older = roadmap?.lifecycle === 'superseded';
  const field = 'mt-1.5 h-11 w-full rounded-xl border-[1.5px] border-slate-300 bg-white px-3 text-sm text-ink focus:border-brand focus:outline-none focus:ring-4 focus:ring-brand-soft';
  const labelCls = 'flex flex-col text-sm font-semibold text-slate-800';

  // Group scheduled tasks by their starting week for the timeline.
  const weekGroups = [];
  scheduled.forEach((it) => {
    const key = it.start_week ?? 0;
    let g = weekGroups.find((x) => x.week === key);
    if (!g) { g = { week: key, items: [] }; weekGroups.push(g); }
    g.items.push(it);
  });
  weekGroups.sort((a, b) => a.week - b.week);
  const isDone = (it) => it.status === 'completed' || it.status === 'skipped';
  const currentWeek = weekGroups.find((g) => g.items.some((it) => !isDone(it)))?.week;
  const pct = p ? Math.round(p.percent_complete) : 0;

  const createForm = (
    <div className="flex flex-col gap-3">
      {analyses.length === 0 ? (
        <p className="m-0 text-sm text-muted">
          You need a completed analysis first. <Link to="/skill-gap" className="font-semibold text-brand underline">Run a skill gap analysis</Link>.
        </p>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          <label className={`${labelCls} col-span-2`}>Analysis
            <select value={form.analysis_id} onChange={set('analysis_id')} className={field}>
              <option value="">Select an analysis…</option>
              {analyses.map((a) => (
                <option key={a.id} value={a.id}>
                  Analysis #{a.id} · job #{a.job_description_id} · alignment {a.overall_alignment_score ?? '—'}%
                </option>
              ))}
            </select>
          </label>
          <label className={labelCls}>Hours per week (1–40)
            <input type="number" min="1" max="40" value={form.hours_per_week} onChange={set('hours_per_week')} className={field} />
          </label>
          <label className={labelCls}>Weeks (1–26)
            <input type="number" min="1" max="26" value={form.duration_weeks} onChange={set('duration_weeks')} className={field} />
          </label>
          <label className={labelCls}>Your level
            <select value={form.experience_level} onChange={set('experience_level')} className={field}>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </label>
          <label className={labelCls}>Learning style
            <select value={form.learning_style} onChange={set('learning_style')} className={field}>
              <option value="balanced">Balanced</option>
              <option value="hands_on">Hands-on first</option>
              <option value="theory_first">Theory first</option>
            </select>
          </label>
          <button type="button" onClick={handleCreate} disabled={!form.analysis_id || creating} className="btn-primary col-span-2">
            {creating ? 'Building your roadmap…' : 'Create roadmap'}
          </button>
        </div>
      )}
      {creating && (
        <p className="m-0 animate-pulse text-sm text-muted">
          Planning your schedule and writing the study plan. This can take up to a minute when the AI service is busy. Please keep this page open.
        </p>
      )}
    </div>
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow m-0">Roadmap</p>
          <h1 className="page-title mt-1">Your learning roadmap</h1>
          <p className="mt-1 text-muted">A week-by-week plan to close your skill gaps, built around the time you have.</p>
        </div>
        {roadmap && (
          <div className="flex flex-wrap items-center gap-2">
            {roadmaps.length > 1 && (
              <>
                <label htmlFor="rm-pick" className="sr-only">Roadmap</label>
                <select id="rm-pick" value={roadmap.id} onChange={(e) => open(e.target.value)}
                  className="h-11 max-w-xs rounded-xl border-[1.5px] border-slate-300 bg-white px-3 text-sm font-semibold">
                  {roadmaps.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.title} · #{r.id} · {new Date(r.created_at).toLocaleDateString()}{r.lifecycle === 'superseded' ? ' (older version)' : ''}
                    </option>
                  ))}
                </select>
              </>
            )}
            <button type="button" onClick={handleDelete} className="btn-secondary text-red-700">Delete</button>
          </div>
        )}
      </div>

      {error && <p role="alert" className="m-0 rounded-xl bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">{error}</p>}

      {!roadmap && (
        <section className="card flex flex-col gap-4">
          <h2 className="m-0 font-display text-lg font-bold">Create your roadmap</h2>
          {createForm}
        </section>
      )}

      {roadmap && (
        <>
          <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="card flex items-center gap-4 p-4 md:col-span-1">
              <svg width="64" height="64" viewBox="0 0 64 64" role="img" aria-label={`${pct}% of tasks complete`}>
                <circle cx="32" cy="32" r="26" fill="none" stroke="#E2E8F0" strokeWidth="8" />
                <circle cx="32" cy="32" r="26" fill="none" stroke="#16A34A" strokeWidth="8" strokeLinecap="round"
                  strokeDasharray={`${(163.4 * pct) / 100} 163.4`} transform="rotate(-90 32 32)" />
                <text x="32" y="37" textAnchor="middle" fontSize="15" fontWeight="700" fill="#0F172A" fontFamily="Space Grotesk, Inter, sans-serif">{pct}%</text>
              </svg>
              <div><p className="eyebrow m-0">Complete</p><p className="m-0 font-semibold">{p?.completed_items ?? 0} of {p?.total_items ?? 0} tasks</p></div>
            </div>
            <div className="card p-4"><p className="eyebrow m-0">Current week</p><p className="m-0 mt-1 font-display text-2xl font-bold">{currentWeek ? `Week ${currentWeek}` : 'All done'}<span className="text-base font-semibold text-muted"> / {roadmap.duration_weeks}</span></p></div>
            <div className="card p-4"><p className="eyebrow m-0">Weekly time</p><p className="m-0 mt-1 font-display text-2xl font-bold">{roadmap.hours_per_week} h</p></div>
            <div className="card p-4"><p className="eyebrow m-0">Planned</p><p className="m-0 mt-1 font-display text-2xl font-bold">≈{roadmap.total_estimated_hours} h<span className="text-base font-semibold text-muted"> / {roadmap.capacity_hours} h</span></p></div>
          </section>

          <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
            <section className="flex flex-col gap-4">
              <div className="card flex flex-col gap-2">
                <h2 className="m-0 font-display text-xl font-bold">{roadmap.title}</h2>
                {roadmap.summary && <p className="m-0 leading-relaxed text-slate-700">{roadmap.summary}</p>}
                {roadmap.feasibility_note && roadmap.feasibility_note !== roadmap.summary && (
                  <p className="m-0 rounded-xl bg-amber-50 px-3.5 py-2.5 text-sm text-amber-900">{roadmap.feasibility_note}</p>
                )}
                {older && <p className="m-0 rounded-xl bg-slate-100 px-3.5 py-2.5 text-sm text-slate-700">This is an older version, kept for history. Open the newest version in the list above to keep working.</p>}
                {roadmap.source_analysis_changed && !older && (
                  <p className="m-0 rounded-xl bg-amber-50 px-3.5 py-2.5 text-sm text-amber-900">Your skill gap analysis has changed since this roadmap was created. Use “Update this plan” to reflect it.</p>
                )}
                {roadmap.generation_source !== 'gemini' && scheduled.some((i) => i.start_week) && (
                  <p className="m-0 text-sm text-muted">Standard study-plan wording was used because the AI service was unavailable. The schedule is not affected.</p>
                )}
                {p && (
                  <div className="mt-1">
                    <div className="h-2.5 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-verified" style={{ width: `${p.percent_complete}%` }} /></div>
                    <p className="m-0 mt-1.5 text-xs text-muted">
                      {p.completed_items} of {p.total_items} tasks completed ({p.percent_complete}%)
                      {p.deferred_items > 0 && ` · ${p.deferred_items} did not fit your time budget`}
                      {p.skipped_items > 0 && ` · ${p.skipped_items} skipped`}. This tracks your roadmap tasks only, not skill level or job readiness.
                    </p>
                  </div>
                )}
              </div>

              <ol className="relative m-0 flex list-none flex-col gap-3 p-0">
                {weekGroups.map((g) => {
                  const done = g.items.every(isDone);
                  const current = g.week === currentWeek;
                  return (
                    <li key={g.week} className="relative pl-14">
                      <span aria-hidden="true" className="absolute bottom-[-12px] left-[21px] top-0 w-0.5 bg-slate-200" />
                      <span className={`absolute left-0 top-3 flex h-11 w-11 items-center justify-center rounded-full font-display text-sm font-bold ${done ? 'bg-verified text-white' : current ? 'bg-brand text-white ring-4 ring-brand-soft' : 'bg-white text-slate-600 ring-2 ring-slate-300'}`}>
                        {done ? '✓' : g.week ? `W${g.week}` : '—'}
                      </span>
                      <details open={current} className="group rounded-2xl bg-white shadow-[0_1px_3px_rgba(15,23,42,.06)]">
                        <summary className="flex min-h-16 cursor-pointer list-none items-center justify-between gap-3 px-5 py-3">
                          <span>
                            <span className="font-display text-lg font-bold">{g.week ? `Week ${g.week}` : 'Carried over'}</span>
                            <span className="ml-2 text-sm text-muted">{g.items.map((i) => i.skill_name).join(' · ')}</span>
                          </span>
                          <span className="flex flex-none items-center gap-2">
                            {current && <span className="rounded-full bg-brand-soft px-2.5 py-1 text-xs font-bold text-brand-dark">Current week</span>}
                            <span className="text-xs font-semibold text-muted">{g.items.filter(isDone).length}/{g.items.length} done</span>
                            <svg className="transition group-open:rotate-180" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#475569" strokeWidth="2" aria-hidden="true"><path d="M6 9l6 6 6-6" /></svg>
                          </span>
                        </summary>
                        <div className="flex flex-col gap-3 px-4 pb-4">
                          {g.items.map((item) => (
                            <RoadmapItemCard key={item.id} item={item} onStatus={handleStatus} busy={busyItem === item.id} readOnly={older} />
                          ))}
                        </div>
                      </details>
                    </li>
                  );
                })}
              </ol>

              {deferred.length > 0 && (
                <section className="card flex flex-col gap-3">
                  <h3 className="m-0 font-display text-lg font-bold">Did not fit your time budget</h3>
                  {deferred.map((item) => (
                    <RoadmapItemCard key={item.id} item={item} onStatus={handleStatus} busy={false} readOnly={older} />
                  ))}
                </section>
              )}
            </section>

            <aside className="flex flex-col gap-4">
              {!older && roadmap.generation_source !== 'gemini' && scheduled.some((i) => i.start_week && !isDone(i)) && (
                <section className="card flex flex-col gap-2">
                  <h3 className="m-0 font-display text-base font-bold">Improve the wording with AI</h3>
                  <p className="m-0 text-sm text-muted">Only the wording of your open tasks is rewritten; the schedule stays the same.</p>
                  <button type="button" onClick={handleImprove} disabled={improving} className="btn-secondary self-start">
                    {improving ? 'Asking the AI service…' : 'Improve with AI'}
                  </button>
                  {improving && <p className="m-0 text-sm text-muted">This can take up to a minute. Please keep this page open.</p>}
                </section>
              )}
              {!older && (
                <section className="card flex flex-col gap-3">
                  <h3 className="m-0 font-display text-base font-bold">Update this plan</h3>
                  <p className="m-0 text-sm text-muted">Rebuilds the plan from your latest gap analysis. The current version is kept as history.</p>
                  <label className={labelCls}>What to keep
                    <select value={upd.mode} onChange={(e) => setUpd({ ...upd, mode: e.target.value })} className={field}>
                      <option value="adapt">Keep my progress</option>
                      <option value="fresh">Start over</option>
                    </select>
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <label className={labelCls}>Hours / week
                      <input type="number" min="1" max="40" placeholder={`${roadmap.hours_per_week} (same)`} value={upd.hours}
                        onChange={(e) => setUpd({ ...upd, hours: e.target.value })} className={field} />
                    </label>
                    <label className={labelCls}>Weeks
                      <input type="number" min="1" max="26" placeholder={`${roadmap.duration_weeks} (same)`} value={upd.weeks}
                        onChange={(e) => setUpd({ ...upd, weeks: e.target.value })} className={field} />
                    </label>
                  </div>
                  <button type="button" onClick={handleUpdate} disabled={updating} className="btn-primary">
                    {updating ? 'Updating…' : 'Update roadmap'}
                  </button>
                  {updating && <p className="m-0 animate-pulse text-sm text-muted">Rebuilding your plan. This can take up to a minute. Please keep this page open.</p>}
                </section>
              )}
              <details className="card">
                <summary className="cursor-pointer list-none font-display text-base font-bold">+ Create another roadmap</summary>
                <div className="mt-3">{createForm}</div>
              </details>
            </aside>
          </div>
        </>
      )}
    </div>
  );
}
