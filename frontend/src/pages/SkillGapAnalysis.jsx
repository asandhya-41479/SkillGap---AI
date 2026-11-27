import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { getJobs } from '../api/jobs';
import { runGapAnalysis, listAnalyses, getAnalysisResults } from '../api/skillGap';
import ResultRow from '../components/skillgap/ResultRow';
import PeriodicTable from '../components/skillgap/PeriodicTable';
import RequirementDonut from '../components/charts/RequirementDonut';
import AreaRadar from '../components/charts/AreaRadar';
import { STATUS, WEIGHT, countBy, statusOf, areaCoverage, sortByPriority, latestAnalysisFor, importanceOf, fmtPct } from '../lib/gap';

const LANES = [
  { key: 'high', title: 'High priority', tint: 'bg-orange-50', badge: 'bg-high text-white' },
  { key: 'medium', title: 'Medium priority', tint: 'bg-amber-50', badge: 'bg-amber-400 text-ink' },
  { key: 'low', title: 'Low priority', tint: 'bg-slate-100', badge: 'bg-slate-300 text-ink' },
];

export default function SkillGapAnalysis() {
  const [jobs, setJobs] = useState([]);
  const [analyses, setAnalyses] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState('');
  const [analysis, setAnalysis] = useState(null); // { id, overall_alignment_score, created_at, results }
  const [booting, setBooting] = useState(true);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');

  // Load jobs + previous analyses; pre-select the job analysed most recently.
  useEffect(() => {
    Promise.all([getJobs(), listAnalyses()])
      .then(([j, a]) => {
        setJobs(j.data);
        setAnalyses(a.data);
        const newest = [...a.data].sort((x, y) => new Date(y.created_at) - new Date(x.created_at))[0];
        if (newest) setSelectedJobId(String(newest.job_description_id));
        else if (j.data[0]) setSelectedJobId(String(j.data[0].id));
      })
      .catch(() => setError('Could not load your jobs. Please refresh the page.'))
      .finally(() => setBooting(false));
  }, []);

  // When the job changes, show its latest saved analysis (no new analysis is run).
  useEffect(() => {
    if (!selectedJobId) return;
    const latest = latestAnalysisFor(analyses, selectedJobId);
    setAnalysis(null);
    if (!latest) return;
    setLoading(true);
    getAnalysisResults(latest.id)
      .then((res) => setAnalysis({ ...latest, results: res.data }))
      .catch(() => setError('Could not load the saved analysis.'))
      .finally(() => setLoading(false));
  }, [selectedJobId, analyses]);

  const handleRun = async () => {
    if (!selectedJobId) return;
    setRunning(true);
    setError('');
    try {
      const res = await runGapAnalysis(selectedJobId);
      setAnalysis(res.data);
      setAnalyses((prev) => [res.data, ...prev.filter((a) => a.id !== res.data.id)]);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.');
    } finally {
      setRunning(false);
    }
  };

  const results = useMemo(() => sortByPriority(analysis?.results || []), [analysis]);
  const counts = useMemo(() => countBy(results), [results]);
  const areas = useMemo(() => areaCoverage(results), [results]);
  const job = jobs.find((j) => String(j.id) === String(selectedJobId));
  const weighted = results.reduce((s, r) => s + (WEIGHT[importanceOf(r)] ?? 0), 0);

  if (booting) return <p className="text-muted">Loading your skill gap…</p>;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow m-0">Skill Gap</p>
          <h1 className="page-title mt-1">Skill Gap Analysis</h1>
          <p className="mt-1 text-muted">Compare your skills with every requirement of a job and see what to close first.</p>
        </div>
        {jobs.length > 0 && (
          <div className="flex flex-wrap items-center gap-3">
            <label htmlFor="job" className="sr-only">Job</label>
            <select id="job" value={selectedJobId} onChange={(e) => setSelectedJobId(e.target.value)}
              className="h-11 min-w-56 rounded-xl border-[1.5px] border-slate-300 bg-white px-3 text-sm font-semibold text-ink focus:border-brand focus:outline-none focus:ring-4 focus:ring-brand-soft">
              {jobs.map((j) => <option key={j.id} value={j.id}>{j.title || j.target_role} (#{j.id})</option>)}
            </select>
            <button type="button" onClick={handleRun} disabled={!selectedJobId || running} className="btn-secondary">
              {running ? 'Analysing…' : analysis ? 'Re-analyse' : 'Run analysis'}
            </button>
            {analysis && <Link to="/roadmap" className="btn-primary">Build roadmap</Link>}
          </div>
        )}
      </div>

      {error && <p role="alert" className="m-0 rounded-xl bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">{error}</p>}

      {jobs.length === 0 && (
        <div className="card text-center">
          <h2 className="m-0 font-display text-xl font-bold">No jobs yet</h2>
          <p className="mt-2 text-muted">Add a job description first, then come back to compare your skills with it.</p>
          <Link to="/jobs" className="btn-primary mt-4">Add a job</Link>
        </div>
      )}

      {jobs.length > 0 && !analysis && !loading && (
        <div className="card text-center">
          <h2 className="m-0 font-display text-xl font-bold">No analysis for this job yet</h2>
          <p className="mt-2 text-muted">Run an analysis to compare your skills with {job?.title || job?.target_role || 'this job'}.</p>
          <button type="button" onClick={handleRun} disabled={running} className="btn-primary mt-4">{running ? 'Analysing…' : 'Run analysis'}</button>
        </div>
      )}

      {loading && <p className="text-muted">Loading the saved analysis…</p>}

      {analysis && (
        <>
          <section className="card grid items-center gap-6 md:grid-cols-[auto_1fr]">
            <RequirementDonut counts={counts} centre={fmtPct(analysis.overall_alignment_score)} caption="alignment" />
            <div className="flex flex-col gap-4">
              <div>
                <h2 className="m-0 font-display text-2xl font-bold">{job?.title || job?.target_role}</h2>
                <p className="mt-1 text-sm text-muted">
                  {results.length} requirements · weighted total {weighted} points (required ×2, preferred ×1, optional ×0.5).
                  Alignment measures how closely your skills match — it is not a hiring probability.
                </p>
              </div>
              <ul className="m-0 grid list-none grid-cols-2 gap-3 p-0 sm:grid-cols-4">
                {['strong', 'high', 'medium', 'low'].map((k) => (
                  <li key={k} className="rounded-xl bg-slate-50 p-3">
                    <span className="flex items-center gap-2 text-xs font-bold text-muted"><span className="h-2.5 w-2.5 rounded-full" style={{ background: STATUS[k].fill }} />{STATUS[k].label}</span>
                    <b className="mt-1 block font-display text-2xl">{counts[k]}</b>
                  </li>
                ))}
              </ul>
            </div>
          </section>

          <div className="grid gap-6 lg:grid-cols-[1fr_1.4fr]">
            <section className="card flex flex-col gap-3">
              <h2 className="m-0 font-display text-lg font-bold">You vs the job, by skill area</h2>
              <div className="flex justify-center"><AreaRadar areas={areas} /></div>
              <div className="flex flex-wrap gap-4 text-[13px] text-slate-700">
                <span className="flex items-center gap-2"><span className="h-1 w-5 rounded bg-brand" />You</span>
                <span className="flex items-center gap-2"><span className="w-5 border-t-[3px] border-dashed border-orange-500" />The job</span>
                <span className="text-muted">Strong = full, partial = half</span>
              </div>
            </section>
            <section className="card flex flex-col gap-3">
              <h2 className="m-0 font-display text-lg font-bold">Every requirement at a glance</h2>
              <PeriodicTable results={results} />
            </section>
          </div>

          <section aria-label="Gaps by priority" className="grid gap-4 lg:grid-cols-3">
            {LANES.map((lane) => {
              const items = results.filter((r) => statusOf(r) === lane.key);
              return (
                <div key={lane.key} className={`flex flex-col gap-3 rounded-2xl p-4 ${lane.tint}`}>
                  <div className="flex items-center justify-between">
                    <h3 className="m-0 font-display text-lg font-bold">{lane.title}</h3>
                    <span className={`rounded-full px-2.5 py-0.5 text-sm font-bold ${lane.badge}`}>{items.length}</span>
                  </div>
                  {items.length === 0 && <p className="m-0 text-sm text-muted">Nothing here.</p>}
                  {items.map((r) => <ResultRow key={r.id} result={r} />)}
                </div>
              );
            })}
          </section>

          <section className="card flex flex-col gap-3">
            <div className="flex items-baseline justify-between">
              <h2 className="m-0 font-display text-lg font-bold">Already strong</h2>
              <span className="text-sm text-muted">{counts.strong} of {results.length}</span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {results.filter((r) => statusOf(r) === 'strong').map((r) => <ResultRow key={r.id} result={r} />)}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
