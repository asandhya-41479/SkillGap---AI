import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getJobs } from '../api/jobs';
import { listAnalyses } from '../api/skillGap';
import {
  generateCareerPlan, generateInterviewPrep, getCareerPlan, getInterviewPrep, updateCareerAction, updateInterviewItem,
} from '../api/career';
import StatusCard from '../components/career/StatusCard';
import ActionCard from '../components/career/ActionCard';
import SkillPriorities from '../components/career/SkillPriorities';
import EvidenceGaps from '../components/career/EvidenceGaps';
import ProjectCards from '../components/career/ProjectCards';
import InterviewPrep from '../components/career/InterviewPrep';
import OpportunityMatcher from '../components/career/OpportunityMatcher';
import { errorText } from '../components/readiness/labels';

// Module 7: Career Intelligence. The plan (status, actions, priorities, evidence gaps, projects,
// interview topics) is built on the backend from Modules 3-6 and cached; this page only loads it,
// shows WHY each action exists, and sends the user's own status changes. A stored plan opens instantly;
// it is rebuilt only when the user's data changed (stale) and they ask for it.

const newestFirst = (a, b) => new Date(b.created_at) - new Date(a.created_at) || b.id - a.id;

export default function CareerIntelligence() {
  const [jobs, setJobs] = useState([]);
  const [analyses, setAnalyses] = useState([]);
  const [jobId, setJobId] = useState('');
  const [plan, setPlan] = useState(null);
  const [prep, setPrep] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [prepRefreshing, setPrepRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

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

  const latest = analyses.find((a) => String(a.job_description_id) === String(jobId)) || null;

  const loadPlan = useCallback(async () => {
    if (!latest) return;
    const [p, i] = await Promise.allSettled([getCareerPlan(latest.id), getInterviewPrep(latest.id)]);
    if (p.status === 'fulfilled') setPlan(p.value.data);
    else setError(errorText(p.reason, 'Could not load your career plan.'));
    setPrep(i.status === 'fulfilled' ? i.value.data : null);
    setLoading(false);
  }, [latest]);

  useEffect(() => {
    setLoading(true);
    setError('');
    setPlan(null);
    setPrep(null);
    loadPlan();
  }, [loadPlan]);

  const refreshPlan = async () => {
    setRefreshing(true);
    setError('');
    try {
      setPlan((await generateCareerPlan(latest.id)).data);
    } catch (err) {
      setError(errorText(err, 'Could not update your career plan.'));
    } finally {
      setRefreshing(false);
    }
  };

  // Closed loop: a completed action with a link becomes Module 6 evidence. When that changed the inputs,
  // the plan is rebuilt straight away so the user sees readiness and next actions update.
  const onUpdateAction = async (actionId, data) => {
    const r = await updateCareerAction(actionId, data);  // errors are shown on the card
    if (r.data.loop_message) setNotice(r.data.loop_message);
    if (r.data.plan_stale) {
      setRefreshing(true);
      try {
        setPlan((await generateCareerPlan(latest.id)).data);
      } finally {
        setRefreshing(false);
      }
    } else {
      setPlan((await getCareerPlan(latest.id)).data);
    }
  };

  const onTogglePrep = async (itemId, status) => {
    await updateInterviewItem(itemId, status);
    const [i, p] = await Promise.all([getInterviewPrep(latest.id), getCareerPlan(latest.id)]);
    setPrep(i.data);
    setPlan(p.data);                                     // interview progress feeds the career status
  };

  const refreshPrep = async () => {
    setPrepRefreshing(true);
    try {
      setPrep((await generateInterviewPrep(latest.id)).data);
    } catch (err) {
      setError(errorText(err, 'Could not update interview topics.'));
    } finally {
      setPrepRefreshing(false);
    }
  };

  const jobName = (id) => {
    const j = jobs.find((x) => String(x.id) === String(id));
    return j ? (j.title || j.target_role) : `Job #${id}`;
  };
  const jobIds = [...new Set(analyses.map((a) => String(a.job_description_id)))];
  const topIds = new Set((plan?.top_actions || []).map((a) => a.id));
  const otherActions = (plan?.actions || []).filter((a) => !topIds.has(a.id));

  // Download the ranked action list as a plain-text checklist (made in the browser, no server call).
  const exportChecklist = () => {
    if (!plan) return;
    const line = (a, i) => `[${a.status === 'COMPLETED' ? 'x' : a.status === 'SKIPPED' ? '-' : ' '}] ${i + 1}. ${a.title} (${String(a.priority).toLowerCase()} priority)\n    Why: ${a.reason}`;
    const text = [
      'SkillGap AI - Career action checklist',
      `Target role: ${plan.target_role}`,
      `Career status: ${plan.career_status.replace(/_/g, ' ').toLowerCase()}`,
      `Readiness: ${plan.readiness_score === null ? 'not enough data' : `${Math.round(plan.readiness_score)}/100`}`,
      `Exported: ${new Date().toLocaleString()}`,
      '',
      'TOP ACTIONS',
      ...plan.top_actions.map(line),
      '',
      'ALL ACTIONS',
      ...plan.actions.map(line),
    ].join('\n');
    const url = URL.createObjectURL(new Blob([text], { type: 'text/plain' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = `skillgap-career-checklist-${plan.target_role.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow m-0">Career Intelligence</p>
          <h1 className="page-title mt-1">Your career action plan</h1>
          <p className="mt-1 text-muted">What to do next to become more competitive for your target role, and why.</p>
        </div>
        {analyses.length > 0 && (
          <div className="flex flex-wrap items-center gap-3">
            <label htmlFor="ci-job" className="sr-only">Target role</label>
            <select id="ci-job" value={jobId} onChange={(e) => setJobId(e.target.value)}
              className="h-11 rounded-xl border-[1.5px] border-slate-300 bg-white px-3 text-sm font-semibold">
              {jobIds.map((id) => <option key={id} value={id}>{jobName(id)} (#{id})</option>)}
            </select>
            {plan && <button type="button" onClick={exportChecklist} className="btn-secondary">Export checklist</button>}
          </div>
        )}
      </div>

      {!loading && analyses.length === 0 ? (
        <div className="card text-center">
          <h2 className="m-0 font-display text-xl font-bold">No analysis yet</h2>
          <p className="mt-2 text-muted">Your career plan is built from a completed skill gap analysis.</p>
          <Link to="/skill-gap" className="btn-primary mt-4">Run a skill gap analysis</Link>
        </div>
      ) : (
        <>
          {error && <p role="alert" className="m-0 rounded-xl bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">{error}</p>}
          {loading && <p className="text-muted">Building your career plan…</p>}

          {!loading && plan && (
            <>
              {plan.stale && (
                <div className="flex flex-wrap items-center gap-3 rounded-xl bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">
                  <span>Your progress, evidence or analysis changed since this plan was built.</span>
                  <button type="button" onClick={refreshPlan} disabled={refreshing} className="btn-primary ml-auto min-h-9">
                    {refreshing ? 'Updating…' : 'Refresh plan'}
                  </button>
                </div>
              )}

              {notice && (
                <div role="status" className="flex items-start gap-2 rounded-xl bg-green-50 px-4 py-3 text-sm font-semibold text-green-800">
                  <span className="flex-1">{notice}{refreshing ? ' Updating your plan…' : ''}</span>
                  <button type="button" onClick={() => setNotice('')} className="h-7 w-7 rounded-lg hover:bg-green-100" aria-label="Dismiss">✕</button>
                </div>
              )}

              <StatusCard plan={plan} />

              <div className="grid gap-6 xl:grid-cols-[1fr_380px]">
                <section className="card flex flex-col gap-3">
                  <div className="flex items-baseline justify-between gap-3">
                    <h2 className="m-0 font-display text-lg font-bold">Your next {plan.top_actions.length} actions</h2>
                    <span className="text-xs text-muted">Plan built {new Date(plan.generated_at).toLocaleString()}</span>
                  </div>
                  {plan.top_actions.length ? (
                    <div className="flex flex-col gap-2.5">
                      {plan.top_actions.map((a, i) => <ActionCard key={a.id} action={a} rank={i + 1} onUpdate={onUpdateAction} />)}
                    </div>
                  ) : (
                    <p className="m-0 text-sm text-slate-700">No open actions. Refresh the plan after your next analysis.</p>
                  )}
                  {otherActions.length > 0 && (
                    <details className="mt-1">
                      <summary className="cursor-pointer text-sm font-semibold text-brand">All actions ({plan.actions.length}, including completed)</summary>
                      <div className="mt-2 flex flex-col gap-2.5">
                        {otherActions.map((a) => <ActionCard key={a.id} action={a} onUpdate={onUpdateAction} />)}
                      </div>
                    </details>
                  )}
                </section>

                {plan.next_milestone && (
                  <section className="card flex flex-col gap-2 self-start bg-navy text-white">
                    <span className="self-start rounded-full bg-orange-500 px-3 py-1 text-xs font-bold text-ink">Next milestone</span>
                    <h2 className="m-0 mt-1 font-display text-xl font-bold leading-snug">{plan.next_milestone.title}</h2>
                    <p className="m-0 text-sm leading-relaxed text-blue-100">{plan.next_milestone.reason}</p>
                  </section>
                )}
              </div>

              <ProjectCards projects={plan.projects} />
              <SkillPriorities rows={plan.skill_priorities} />
              <EvidenceGaps gaps={plan.evidence_gaps} />
              <InterviewPrep prep={prep} onToggle={onTogglePrep} onRefresh={refreshPrep} refreshing={prepRefreshing} />
            </>
          )}
        </>
      )}

      <OpportunityMatcher />
    </div>
  );
}
