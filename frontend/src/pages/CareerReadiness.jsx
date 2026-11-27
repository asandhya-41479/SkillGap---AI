import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getJobs } from '../api/jobs';
import { listAnalyses } from '../api/skillGap';
import { getRoadmap } from '../api/roadmaps';
import { listEvidence } from '../api/evidence';
import { calculateReadiness, compareAnalyses, getLatestReadinessForJob, getReadinessHistory } from '../api/readiness';
import ScoreSummary from '../components/readiness/ScoreSummary';
import NextActionCard from '../components/readiness/NextActionCard';
import SkillSections from '../components/readiness/SkillSections';
import ComparisonCard from '../components/readiness/ComparisonCard';
import EvidencePanel from '../components/readiness/EvidencePanel';
import HistoryTrend from '../components/readiness/HistoryTrend';
import { errorText } from '../components/readiness/labels';

// Module 6 dashboard. All scores, components, gaps and the next action come from the backend;
// this page only loads, displays and triggers recalculation. A saved snapshot is shown instantly,
// and recalculation runs only when the user asks (or when no score exists yet).

const newestFirst = (a, b) => new Date(b.created_at) - new Date(a.created_at) || b.id - a.id;
const lastScoreFor = (points, analysisId) => {
  const p = [...points].reverse().find((x) => x.analysis_id === analysisId && x.score !== null);
  return p ? p.score : null;
};

export default function CareerReadiness() {
  const [jobs, setJobs] = useState([]);
  const [analyses, setAnalyses] = useState([]);       // completed only, newest first
  const [jobId, setJobId] = useState('');
  const [snap, setSnap] = useState(null);             // latest saved readiness for the job (null = none yet)
  const [history, setHistory] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [evidence, setEvidence] = useState([]);
  const [roadmapItems, setRoadmapItems] = useState({});
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [error, setError] = useState('');
  const [preset, setPreset] = useState(null);

  // ---- first load: jobs + completed analyses; default to the job analysed most recently
  useEffect(() => {
    Promise.all([getJobs(), listAnalyses()])
      .then(([j, a]) => {
        const done = a.data.filter((x) => x.status === 'completed').sort(newestFirst);
        setJobs(j.data);
        setAnalyses(done);
        if (done.length) setJobId(String(done[0].job_description_id));
        else setLoading(false);
      })
      .catch(() => {
        setError('Could not load your jobs and analyses.');
        setLoading(false);
      });
  }, []);

  const jobAnalyses = analyses.filter((a) => String(a.job_description_id) === String(jobId));
  const latest = jobAnalyses[0] || null;
  const previous = jobAnalyses[1] || null;

  // ---- everything for one job; each part fails on its own so one error never blanks the page
  const loadJob = useCallback(async () => {
    if (!jobId) return;
    setError('');
    const list = analyses.filter((a) => String(a.job_description_id) === String(jobId));
    const [cur, prev] = [list[0], list[1]];

    const [s, h, e, c] = await Promise.allSettled([
      getLatestReadinessForJob(jobId),
      getReadinessHistory(jobId),
      listEvidence(),
      prev && cur ? compareAnalyses(prev.id, cur.id) : Promise.resolve(null),
    ]);

    const latestSnap = s.status === 'fulfilled' ? s.value.data : null;
    if (s.status === 'rejected' && s.reason?.response?.status !== 404) {
      setError(errorText(s.reason, 'Could not load your readiness score.'));
    }
    setSnap(latestSnap);
    setHistory(h.status === 'fulfilled' ? h.value.data : null);
    setEvidence(e.status === 'fulfilled' ? e.value.data : []);
    setComparison(c.status === 'fulfilled' && c.value ? c.value.data : null);

    // Roadmap tasks let gap alerts say "Complete the Docker task (week 4)". Optional: ignore errors.
    let items = {};
    if (latestSnap?.roadmap_id) {
      try {
        const rm = (await getRoadmap(latestSnap.roadmap_id)).data;
        items = Object.fromEntries(rm.items.map((i) => [i.skill_name.toLowerCase(), i]));
      } catch { /* roadmap deleted: alerts fall back to evidence advice */ }
    }
    setRoadmapItems(items);
    setLoading(false);
  }, [jobId, analyses]);

  useEffect(() => {
    setLoading(true);
    loadJob();
  }, [loadJob]);

  const handleCalculate = async () => {
    if (!latest) return;
    setCalculating(true);
    setError('');
    try {
      await calculateReadiness(latest.id);
      await loadJob();
    } catch (err) {
      setError(errorText(err, 'Could not calculate readiness. Please try again.'));
    } finally {
      setCalculating(false);
    }
  };

  const jobName = (id) => {
    const j = jobs.find((x) => String(x.id) === String(id));
    return j ? (j.title || j.target_role) : `Job #${id}`;
  };
  const jobIds = [...new Set(analyses.map((a) => String(a.job_description_id)))];
  const points = history?.points || [];
  const newerAnalysis = snap && latest && snap.analysis_id !== latest.id;
  const skills = (snap?.breakdown || []).map((b) => b.skill_name);

  const prevScore = previous ? lastScoreFor(points, previous.id) : null;
  const banner = (tone, text) => (
    <p className={`m-0 rounded-xl px-4 py-3 text-sm font-semibold ${tone === 'warn' ? 'bg-amber-50 text-amber-900' : 'bg-slate-100 text-slate-700'}`}>{text}</p>
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow m-0">Progress &amp; Readiness</p>
          <h1 className="page-title mt-1">How ready are you?</h1>
          <p className="mt-1 text-muted">Your readiness score, what drives it, and how it changed between analyses.</p>
        </div>
        {analyses.length > 0 && (
          <div className="flex flex-wrap items-center gap-3">
            <label htmlFor="rd-job" className="sr-only">Target role</label>
            <select id="rd-job" value={jobId} onChange={(e) => setJobId(e.target.value)}
              className="h-11 rounded-xl border-[1.5px] border-slate-300 bg-white px-3 text-sm font-semibold">
              {jobIds.map((id) => <option key={id} value={id}>{jobName(id)} (#{id})</option>)}
            </select>
            <button type="button" onClick={handleCalculate} disabled={!latest || calculating} className="btn-primary">
              {calculating ? 'Calculating…' : snap ? 'Recalculate readiness' : 'Calculate readiness'}
            </button>
          </div>
        )}
      </div>

      {!loading && analyses.length === 0 ? (
        <div className="card text-center">
          <h2 className="m-0 font-display text-xl font-bold">No analysis yet</h2>
          <p className="mt-2 text-muted">Readiness is calculated from a completed skill gap analysis.</p>
          <Link to="/skill-gap" className="btn-primary mt-4">Run a skill gap analysis</Link>
        </div>
      ) : (
        <>
          {error && <p role="alert" className="m-0 rounded-xl bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">{error}</p>}
          {loading && <p className="text-muted">Loading…</p>}

          {!loading && !snap && latest && (
            <div className="card text-center">
              <h2 className="m-0 font-display text-xl font-bold">No readiness score yet</h2>
              <p className="mt-2 text-muted">Click <b>Calculate readiness</b> to create one from analysis #{latest.id}.</p>
            </div>
          )}

          {!loading && snap && (
            <>
              {newerAnalysis && banner('warn', `A newer gap analysis (#${latest.id}) exists. Recalculate to use it.`)}
              {!newerAnalysis && snap.is_stale && banner('warn', 'Your progress or evidence changed since this score was calculated. Recalculate to update it.')}
              {!snap.source_available && banner('info', 'The analysis behind this score was deleted. The saved score is kept for your history.')}
              <p className="m-0 -mb-3 text-xs text-muted">
                Calculated {new Date(`${snap.snapshot_date}T00:00:00`).toLocaleDateString()} from analysis #{snap.analysis_id ?? '—'}
              </p>

              <ScoreSummary snap={snap} previousScore={prevScore} />
              <div className="grid gap-6 lg:grid-cols-2">
                <ComparisonCard comparison={comparison} hasPrevious={Boolean(previous)}
                  scoreBefore={prevScore} scoreAfter={latest ? lastScoreFor(points, latest.id) : null} />
                <NextActionCard action={snap.next_action} feedback={snap.ai_feedback}
                  onAddEvidence={(skill) => setPreset({ skill, n: Date.now() })} />
              </div>
              <SkillSections breakdown={snap.breakdown} roadmapItems={roadmapItems} />
              {skills.length > 0 && (
                <EvidencePanel skills={skills} evidence={evidence} onChanged={loadJob} preset={preset} />
              )}
              <HistoryTrend history={history} />
            </>
          )}
        </>
      )}
    </div>
  );
}
