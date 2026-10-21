import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { listAnalyses } from '../api/skillGap';
import { createRoadmap, regenerateRoadmap, listRoadmaps, getRoadmap, setItemStatus, deleteRoadmap } from '../api/roadmaps';
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
  const field = 'border rounded px-2 py-1 w-full';

  return (
    <div className="max-w-3xl mx-auto p-6">
      <Link to="/dashboard" className="text-sm text-purple-700 hover:underline">← Dashboard</Link>
      <h1 className="text-2xl font-bold my-3">Skill Gap Roadmap</h1>

      <div className="bg-white border rounded-lg p-4 mb-6">
        {analyses.length === 0 ? (
          <p className="text-sm text-gray-600">
            You need a completed analysis first. <Link to="/skill-gap" className="text-purple-700 underline">Run a skill gap analysis</Link>.
          </p>
        ) : (
          <div className="grid grid-cols-2 gap-3 text-sm">
            <label className="col-span-2">Analysis
              <select value={form.analysis_id} onChange={set('analysis_id')} className={field}>
                <option value="">Select an analysis…</option>
                {analyses.map((a) => (
                  <option key={a.id} value={a.id}>
                    Analysis #{a.id} · job #{a.job_description_id} · alignment {a.overall_alignment_score ?? '—'}%
                  </option>
                ))}

              </select>
            </label>
            <label>Hours per week (1–40)
              <input type="number" min="1" max="40" value={form.hours_per_week} onChange={set('hours_per_week')} className={field} />
            </label>
            <label>Weeks (1–26)
              <input type="number" min="1" max="26" value={form.duration_weeks} onChange={set('duration_weeks')} className={field} />
            </label>
            <label>Your level
              <select value={form.experience_level} onChange={set('experience_level')} className={field}>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </label>
            <label>Learning style
              <select value={form.learning_style} onChange={set('learning_style')} className={field}>
                <option value="balanced">Balanced</option>
                <option value="hands_on">Hands-on first</option>
                <option value="theory_first">Theory first</option>
              </select>
            </label>
            <button
              onClick={handleCreate}
              disabled={!form.analysis_id || creating}
              className="col-span-2 bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 disabled:opacity-50"
            >
              {creating ? 'Building your roadmap…' : 'Create roadmap'}
            </button>
          </div>
        )}
        {creating && (

          <p className="mt-3 text-sm text-gray-600 animate-pulse">
            Planning your schedule and writing the study plan. This can take up to a minute when the AI service is busy — please keep this page open.
          </p>
        )}
      </div>

      {error && <p className="text-red-600 mb-4">{error}</p>}

      {roadmap && (
        <>
          <div className="flex justify-between items-center gap-3 mb-2">
            {roadmaps.length > 1 ? (
              <select value={roadmap.id} onChange={(e) => open(e.target.value)} className="border rounded px-2 py-1 text-sm">
                {roadmaps.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.title} · #{r.id} · {new Date(r.created_at).toLocaleDateString()}{r.lifecycle === 'superseded' ? ' (older version)' : ''}
                  </option>
                ))}
              </select>
            ) : <h2 className="text-xl font-semibold">{roadmap.title}</h2>}
            <button onClick={handleDelete} className="text-sm text-red-600 hover:underline">Delete</button>
          </div>

          <p className="text-sm text-gray-500 mb-2">
            {roadmap.hours_per_week} h/week × {roadmap.duration_weeks} weeks · ≈{roadmap.total_estimated_hours} of {roadmap.capacity_hours} h planned
          </p>
          {roadmap.summary && <p className="mb-2">{roadmap.summary}</p>}
          {roadmap.feasibility_note && roadmap.feasibility_note !== roadmap.summary && (
            <p className="mb-2 text-sm text-amber-700">{roadmap.feasibility_note}</p>
          )}
          {roadmap.generation_source !== 'gemini' && scheduled.some((i) => i.start_week) && (
            <p className="mb-2 text-sm text-gray-500">

              Standard study-plan wording was used because the AI service was unavailable. The schedule is not affected.
            </p>
          )}
          {older && (
            <p className="mb-2 text-sm text-gray-600">
              This is an older version, kept for history. Open the newest version in the list above to keep working.
            </p>
          )}
          {roadmap.source_analysis_changed && !older && (
            <p className="mb-2 text-sm text-amber-700">
              Your skill gap analysis has changed since this roadmap was created. Use “Update this plan” below to reflect it.
            </p>
          )}

          {p && (
            <div className="my-4">
              <div className="h-2 bg-gray-200 rounded">
                <div className="h-2 bg-green-500 rounded" style={{ width: `${p.percent_complete}%` }} />
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {p.completed_items} of {p.total_items} tasks completed ({p.percent_complete}%)
                {p.deferred_items > 0 && ` · ${p.deferred_items} did not fit your time budget`}
                {p.skipped_items > 0 && ` · ${p.skipped_items} skipped`}. This tracks your roadmap tasks only — it is not a measure of
                skill level or job readiness.
              </p>
            </div>
          )}

          {!older && (
            <div className="bg-white border rounded-lg p-4 mb-4 text-sm">
              <strong>Update this plan</strong>
              <p className="text-gray-500">

                Rebuilds the plan from your latest gap analysis. The current version is kept as history.
              </p>
              <div className="grid grid-cols-3 gap-3 mt-2">
                <label>What to keep
                  <select value={upd.mode} onChange={(e) => setUpd({ ...upd, mode: e.target.value })} className={field}>
                    <option value="adapt">Keep my progress</option>
                    <option value="fresh">Start over</option>
                  </select>
                </label>
                <label>Hours per week
                  <input type="number" min="1" max="40" placeholder={`${roadmap.hours_per_week} (same)`} value={upd.hours}
                    onChange={(e) => setUpd({ ...upd, hours: e.target.value })} className={field} />
                </label>
                <label>Weeks
                  <input type="number" min="1" max="26" placeholder={`${roadmap.duration_weeks} (same)`} value={upd.weeks}
                    onChange={(e) => setUpd({ ...upd, weeks: e.target.value })} className={field} />
                </label>
              </div>
              <button onClick={handleUpdate} disabled={updating}
                className="mt-3 bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 disabled:opacity-50">
                {updating ? 'Updating…' : 'Update roadmap'}
              </button>
              {updating && (
                <p className="mt-2 text-gray-600 animate-pulse">
                  Rebuilding your plan. This can take up to a minute when the AI service is busy — please keep this page open.
                </p>
              )}
            </div>
          )}

          {scheduled.map((item) => (
            <RoadmapItemCard key={item.id} item={item} onStatus={handleStatus} busy={busyItem === item.id} readOnly={older} />

          ))}

          {deferred.length > 0 && (
            <>
              <h3 className="mt-6 mb-2 font-semibold">Did not fit your time budget</h3>
              {deferred.map((item) => (
                <RoadmapItemCard key={item.id} item={item} onStatus={handleStatus} busy={false} readOnly={older} />
              ))}
            </>
          )}
        </>
      )}
    </div>
  );
}