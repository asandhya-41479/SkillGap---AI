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

  const onUpdateAction = async (actionId, data) => {
    await updateCareerAction(actionId, data);           // errors are shown on the card
    setPlan((await getCareerPlan(latest.id)).data);
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

  return (
    <div className="max-w-4xl mx-auto p-6">
      <Link to="/dashboard" className="text-sm text-purple-700 hover:underline">← Dashboard</Link>
      <h1 className="text-2xl font-bold my-3">Career Intelligence</h1>
      <p className="text-sm text-gray-600 mb-4">
        What to do next to become more competitive for your target role, and why.
      </p>

      {!loading && analyses.length === 0 ? (
        <div className="bg-white border rounded-lg p-4 mb-4">
          <p className="text-sm text-gray-600">
            Your career plan is built from a completed skill gap analysis.{' '}
            <Link to="/skill-gap" className="text-purple-700 underline">Run a skill gap analysis</Link> first.
          </p>
        </div>
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <label className="text-sm">Target role
              <select value={jobId} onChange={(e) => setJobId(e.target.value)} className="border rounded px-2 py-1 ml-2">
                {jobIds.map((id) => <option key={id} value={id}>{jobName(id)} (#{id})</option>)}
              </select>
            </label>
            {plan && (
              <span className="text-xs text-gray-400 ml-auto">
                Plan built {new Date(plan.generated_at).toLocaleString()}
              </span>
            )}
          </div>

          {error && <p className="text-red-600 mb-4">{error}</p>}
          {loading && <p className="text-gray-500">Building your career plan…</p>}

          {!loading && plan && (
            <>
              {plan.stale && (
                <div className="mb-4 text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded p-2 flex items-center gap-2">
                  <span>Your progress, evidence or analysis changed since this plan was built.</span>
                  <button onClick={refreshPlan} disabled={refreshing}
                    className="ml-auto bg-purple-600 text-white px-3 py-1 rounded text-sm disabled:opacity-50">
                    {refreshing ? 'Updating…' : 'Refresh plan'}
                  </button>
                </div>
              )}

              <StatusCard plan={plan} />

              {plan.next_milestone && (
                <div className="bg-white border-2 border-purple-200 rounded-lg p-4 mb-4">
                  <div className="text-xs font-semibold tracking-wide text-purple-700">NEXT MILESTONE</div>
                  <div className="text-lg font-semibold mt-1">{plan.next_milestone.title}</div>
                  <p className="text-sm text-gray-600 mt-1">{plan.next_milestone.reason}</p>
                </div>
              )}

              <div className="bg-white border rounded-lg p-4 mb-4">
                <div className="text-xs font-semibold tracking-wide text-gray-500 mb-2">
                  YOUR NEXT {plan.top_actions.length} ACTIONS
                </div>
                {plan.top_actions.length ? (
                  <div className="space-y-2">
                    {plan.top_actions.map((a, i) => <ActionCard key={a.id} action={a} rank={i + 1} onUpdate={onUpdateAction} />)}
                  </div>
                ) : (
                  <p className="text-sm text-gray-600">No open actions. Refresh the plan after your next analysis.</p>
                )}
                {otherActions.length > 0 && (
                  <details className="mt-3">
                    <summary className="text-sm text-purple-700 cursor-pointer">
                      All actions ({plan.actions.length}, including completed)
                    </summary>
                    <div className="space-y-2 mt-2">
                      {otherActions.map((a) => <ActionCard key={a.id} action={a} onUpdate={onUpdateAction} />)}
                    </div>
                  </details>
                )}
              </div>

              <SkillPriorities rows={plan.skill_priorities} />
              <EvidenceGaps gaps={plan.evidence_gaps} />
              <ProjectCards projects={plan.projects} />
              <InterviewPrep prep={prep} onToggle={onTogglePrep} onRefresh={refreshPrep} refreshing={prepRefreshing} />
            </>
          )}
        </>
      )}

      <OpportunityMatcher />
    </div>
  );
}
