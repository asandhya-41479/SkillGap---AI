import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getJobs } from '../api/jobs';
import { getSkills } from '../api/skills';
import { listAnalyses, getAnalysisResults } from '../api/skillGap';
import { listRoadmaps } from '../api/roadmaps';
import { getLatestReadinessForJob, getReadinessHistory } from '../api/readiness';
import Constellation from '../components/charts/Constellation';
import Gauge from '../components/charts/Gauge';
import TrendLine from '../components/charts/TrendLine';
import { STATUS, countBy, statusOf, nameOf, missingPoints, sortByPriority, fmtPct } from '../lib/gap';

const ACTION_LINK = { roadmap_item: '/roadmap', add_evidence: '/skills', rerun_analysis: '/skill-gap' };

function Step({ n, title, sub, state, to }) {
  const styles = {
    done: 'bg-brand text-white',
    current: 'bg-orange-500 text-white ring-4 ring-orange-100',
    todo: 'bg-white text-slate-500 ring-2 ring-inset ring-slate-300',
  };
  return (
    <li className="relative z-10 flex min-w-0 flex-1 flex-col items-center gap-2 text-center md:min-w-[110px]">
      <Link to={to} className={`flex h-12 w-12 items-center justify-center rounded-2xl font-display text-lg font-bold ${styles[state]}`}
        aria-label={`Step ${n}: ${title} (${state === 'done' ? 'done' : state === 'current' ? 'current step' : 'not started'})`}>
        {state === 'done'
          ? <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" aria-hidden="true"><path d="M5 12l5 5 9-10" /></svg>
          : n}
      </Link>
      <span className={`text-sm font-bold ${state === 'current' ? 'text-orange-700' : 'text-ink'}`}>{title}</span>
      <span className="text-xs text-muted">{sub}</span>
    </li>
  );
}

function Kpi({ label, value, sub, tone = 'text-ink' }) {
  return (
    <div className="rounded-2xl bg-slate-50 p-4">
      <p className="eyebrow m-0">{label}</p>
      <p className={`m-0 mt-1 font-display text-3xl font-bold ${tone}`}>{value}</p>
      {sub && <p className="m-0 mt-0.5 text-xs text-muted">{sub}</p>}
    </div>
  );
}

function Dashboard() {
  const { user } = useAuth();
  const [state, setState] = useState({ loading: true, error: '' });
  const [data, setData] = useState({ jobs: [], skills: [], analyses: [], roadmaps: [] });
  const [focus, setFocus] = useState({ job: null, analysis: null, results: [], readiness: null, history: [] });

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [j, s, a, r] = await Promise.all([getJobs(), getSkills(), listAnalyses(), listRoadmaps()]);
        if (!alive) return;
        setData({ jobs: j.data, skills: s.data, analyses: a.data, roadmaps: r.data });
        const newest = [...a.data].sort((x, y) => new Date(y.created_at) - new Date(x.created_at))[0];
        if (newest) {
          const jobId = newest.job_description_id;
          const [res, rd, hist] = await Promise.all([
            getAnalysisResults(newest.id),
            getLatestReadinessForJob(jobId).catch(() => null),
            getReadinessHistory(jobId).catch(() => null),
          ]);
          if (!alive) return;
          setFocus({
            job: j.data.find((x) => x.id === jobId) || null,
            analysis: newest,
            results: res.data,
            readiness: rd?.data || null,
            history: hist?.data?.points || [],
          });
        }
        setState({ loading: false, error: '' });
      } catch {
        if (alive) setState({ loading: false, error: 'Could not load your dashboard. If the server was asleep, wait 30 seconds and refresh.' });
      }
    })();
    return () => { alive = false; };
  }, []);

  const results = useMemo(() => sortByPriority(focus.results), [focus.results]);
  const counts = useMemo(() => countBy(results), [results]);
  const rd = focus.readiness;
  const scored = focus.history.filter((p) => p.score !== null && p.score !== undefined);
  const previous = scored.length >= 2 ? scored[scored.length - 2].score : null;
  const delta = rd?.score !== null && rd?.score !== undefined && previous !== null ? Math.round((rd.score - previous) * 10) / 10 : null;
  const open = results.filter((r) => statusOf(r) !== 'strong');
  const totalMissing = open.reduce((s, r) => s + missingPoints(r), 0);
  const maxPts = Math.max(...open.map(missingPoints), 1);
  const first = (user?.name || '').split(' ')[0];

  const steps = [
    { title: 'Skill profile', sub: `${data.skills.length} skills`, done: data.skills.length > 0, to: '/skills' },
    { title: 'Target job', sub: `${data.jobs.length} job${data.jobs.length === 1 ? '' : 's'}`, done: data.jobs.length > 0, to: '/jobs' },
    { title: 'Gap analysis', sub: focus.analysis ? `${results.length} requirements` : 'Not run yet', done: !!focus.analysis, to: '/skill-gap' },
    { title: 'Roadmap', sub: data.roadmaps.length ? `${data.roadmaps.length} roadmap${data.roadmaps.length === 1 ? '' : 's'}` : 'Not created', done: data.roadmaps.length > 0, to: '/roadmap' },
    { title: 'Readiness', sub: rd?.score != null ? `${Math.round(rd.score)}/100` : 'Not checked', done: rd?.score != null, to: '/readiness' },
    { title: 'Career plan', sub: 'Next actions', done: false, to: '/career' },
  ];
  const currentIdx = steps.findIndex((s) => !s.done);

  if (state.loading) return <p className="text-muted">Loading your dashboard…</p>;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow m-0">Dashboard</p>
          <h1 className="page-title mt-1">{first ? `Good to see you, ${first}` : 'Welcome back'}</h1>
          <p className="mt-1 text-muted">
            {focus.job ? <>Your latest analysis: <strong className="text-ink">{focus.job.title || focus.job.target_role}</strong></> : 'Start by adding your skills and a target job.'}
          </p>
        </div>
        {focus.analysis && <Link to="/skill-gap" className="btn-secondary">Open full Skill Gap</Link>}
      </div>

      {state.error && <p role="alert" className="m-0 rounded-xl bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">{state.error}</p>}

      <section className="card" aria-label="Your journey">
        <ol className="relative m-0 grid list-none grid-cols-3 gap-y-5 p-0 md:flex md:gap-2">
          <span aria-hidden="true" className="absolute left-[8%] right-[8%] top-6 hidden h-1 rounded bg-slate-200 md:block" />
          <span aria-hidden="true" className="absolute left-[8%] top-6 hidden h-1 rounded bg-brand md:block"
            style={{ width: `${(Math.max(currentIdx === -1 ? 5 : currentIdx, 0) / 5) * 84}%` }} />
          {steps.map((s, i) => (
            <Step key={s.title} n={i + 1} {...s} state={s.done ? 'done' : i === currentIdx ? 'current' : 'todo'} />
          ))}
        </ol>
      </section>

      {!focus.analysis ? (
        <section className="card text-center">
          <h2 className="m-0 font-display text-xl font-bold">Your skill map appears after your first analysis</h2>
          <p className="mt-2 text-muted">Add skills, add a job description, then run a Skill Gap analysis.</p>
          <Link to={steps[currentIdx]?.to || '/skills'} className="btn-primary mt-4">Continue: {steps[currentIdx]?.title || 'Skill profile'}</Link>
        </section>
      ) : (
        <>
          <div className="grid gap-6 xl:grid-cols-[1.35fr_1fr]">
            <section className="card flex flex-col gap-3 bg-night text-white">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="eyebrow m-0 text-cyan-300">Your skill map</p>
                  <h2 className="m-0 mt-1 font-display text-xl font-bold">{results.length} job requirements around you</h2>
                </div>
                <div className="flex flex-wrap gap-3 text-[13px] text-slate-200">
                  {['strong', 'high', 'medium', 'low'].map((k) => (
                    <span key={k} className="flex items-center gap-1.5">
                      <span className="h-2.5 w-2.5 rounded-full" style={{ background: k === 'strong' ? '#22D3EE' : STATUS[k].fill }} />
                      {k === 'strong' ? 'Strong' : `${STATUS[k].label.split(' ')[0]} gap`} ({counts[k]})
                    </span>
                  ))}
                </div>
              </div>
              <Constellation results={results}
                centreValue={rd?.score != null ? rd.score : focus.analysis.overall_alignment_score}
                centreLabel={rd?.score != null ? 'Readiness' : 'Alignment %'} />
              <ul className="m-0 flex list-none flex-wrap gap-1.5 p-0 sm:hidden" aria-label="Requirements by status">
                {results.map((r) => {
                  const st = statusOf(r);
                  return (
                    <li key={r.id} className="rounded-full px-2.5 py-1 text-xs font-semibold"
                      style={{ background: st === 'strong' ? '#0E3A4A' : '#2A1A10', color: st === 'strong' ? '#A5F3FC' : st === 'high' ? '#FDBA74' : st === 'medium' ? '#FCD34D' : '#CBD5E1' }}>
                      {nameOf(r)}
                    </li>
                  );
                })}
              </ul>
            </section>

            <div className="flex flex-col gap-6">
              <section className="card flex flex-col items-center gap-2">
                <div className="flex w-full items-center justify-between">
                  <p className="eyebrow m-0">Career readiness</p>
                  {rd?.label && <span className="rounded-full bg-orange-100 px-3 py-1 text-xs font-bold text-orange-800">{rd.label}</span>}
                </div>
                <Gauge value={rd?.score ?? null} previous={previous} label={rd?.score != null ? 'out of 100' : 'not checked yet'} />
                {delta !== null && (
                  <p className="m-0 text-sm text-muted">
                    <span className={`font-bold ${delta >= 0 ? 'text-green-700' : 'text-red-700'}`}>{delta >= 0 ? '+' : ''}{delta}</span> since your previous check ({Math.round(previous)})
                  </p>
                )}
                {rd?.score == null && <Link to="/readiness" className="btn-secondary mt-1">Check readiness</Link>}
              </section>

              {rd?.next_action && (
                <section className="card flex flex-col gap-3 bg-navy text-white">
                  <span className="self-start rounded-full bg-orange-500 px-3 py-1 text-xs font-bold text-ink">Next best action</span>
                  <h2 className="m-0 font-display text-xl font-bold leading-snug">{rd.next_action.title}</h2>
                  <Link to={ACTION_LINK[rd.next_action.kind] || '/readiness'} className="btn-primary self-start bg-white text-ink hover:bg-blue-50">Do it now</Link>
                </section>
              )}
            </div>
          </div>

          <section className="grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
            <Kpi label="Job alignment" value={fmtPct(focus.analysis.overall_alignment_score)} tone="text-brand" sub="weighted match with the job" />
            <Kpi label="Required covered" value={rd ? `${rd.metrics.required_covered}/${rd.metrics.required_total}` : '—'} sub="required skills strong" />
            <Kpi label="High-priority gaps" value={counts.high} tone="text-high" sub="close these first" />
            <Kpi label="Strong matches" value={`${counts.strong}/${results.length}`} tone="text-verified" sub="requirements" />
          </section>

          <div className="grid gap-6 lg:grid-cols-2">
            <section className="card flex flex-col gap-3">
              <h2 className="m-0 font-display text-lg font-bold">Readiness over time</h2>
              <TrendLine points={focus.history} />
            </section>
            <section className="card flex flex-col gap-3">
              <div className="flex items-baseline justify-between">
                <h2 className="m-0 font-display text-lg font-bold">Points still on the table</h2>
                <span className="text-sm font-semibold text-muted">{totalMissing} weighted points</span>
              </div>
              {open.length === 0 && <p className="m-0 text-muted">No gaps — every requirement is strong.</p>}
              <ul className="m-0 flex list-none flex-col gap-2.5 p-0">
                {open.slice(0, 8).map((r) => (
                  <li key={r.id} className="grid grid-cols-[minmax(0,10rem)_1fr_2.5rem] items-center gap-3 text-sm">
                    <span className="truncate font-semibold">{nameOf(r)}</span>
                    <span className="h-2.5 overflow-hidden rounded-full bg-slate-100">
                      <span className="block h-full rounded-full" style={{ width: `${(missingPoints(r) / maxPts) * 100}%`, background: STATUS[statusOf(r)].fill }} />
                    </span>
                    <span className="text-right font-bold">+{missingPoints(r)}</span>
                  </li>
                ))}
              </ul>
              {open.length > 8 && <Link to="/skill-gap" className="text-sm font-bold text-brand">See all {open.length} gaps →</Link>}
            </section>
          </div>
        </>
      )}
    </div>
  );
}

export default Dashboard;
