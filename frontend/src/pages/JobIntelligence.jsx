import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getJobs, getJob, createJob, deleteJob, analyzeJob } from '../api/jobs';
import JobForm from '../components/jobs/JobForm';
import JobList from '../components/jobs/JobList';
import RequirementsView from '../components/jobs/RequirementsView';

export default function JobIntelligence() {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');

  const loadJobs = async () => {
    try {
      const res = await getJobs();
      setJobs(res.data);
    } catch {
      setError('Failed to load job descriptions.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Open the newest job straight away so its requirements are visible.
    getJobs()
      .then((res) => { if (res.data[0]) handleSelect(res.data[0].id); })
      .catch(() => {});
    loadJobs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSelect = async (id) => {
    setError('');
    try {
      const res = await getJob(id);
      setSelectedJob(res.data);
    } catch {
      setError('Failed to load job details.');
    }
  };

  const handleCreate = async (data) => {
    setSubmitting(true);
    setError('');
    try {
      const res = await createJob(data);
      await loadJobs();
      setSelectedJob(res.data);
    } catch (err) {
      setError(err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || 'Failed to submit job description.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this job description and its requirements?')) return;
    await deleteJob(id);
    if (selectedJob?.id === id) setSelectedJob(null);
    loadJobs();
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setError('');
    try {
      const res = await analyzeJob(selectedJob.id);
      setSelectedJob(res.data);
      loadJobs();
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.');
      handleSelect(selectedJob.id); // refresh to show "failed" status
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) return <p className="text-muted">Loading your jobs…</p>;

  const reqCount = selectedJob?.requirements?.length || 0;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="eyebrow m-0">Job Intelligence</p>
        <h1 className="page-title mt-1">Understand the job you want</h1>
        <p className="mt-1 text-muted">Paste a job description and SkillGap AI turns it into a clear list of requirements.</p>
      </div>
      {error && <p role="alert" className="m-0 rounded-xl bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">{typeof error === 'string' ? error : 'Something went wrong.'}</p>}

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <JobForm onSubmit={handleCreate} submitting={submitting} />
        <section className="card flex flex-col gap-3">
          <div className="flex items-baseline justify-between">
            <h2 className="m-0 font-display text-lg font-bold">Your job descriptions</h2>
            <span className="text-sm text-muted">{jobs.length}</span>
          </div>
          <JobList jobs={jobs} selectedId={selectedJob?.id} onSelect={handleSelect} onDelete={handleDelete} />
        </section>
      </div>

      {selectedJob ? (
        <section className="card flex flex-col gap-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="eyebrow m-0">Extracted requirements</p>
              <h2 className="m-0 mt-1 font-display text-2xl font-bold">{selectedJob.title || selectedJob.target_role}</h2>
              <p className="m-0 mt-1 text-sm text-muted">{selectedJob.target_role} · {reqCount} requirement{reqCount === 1 ? '' : 's'}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={handleAnalyze} disabled={analyzing} className={selectedJob.status === 'analyzed' ? 'btn-secondary' : 'btn-primary'}>
                {analyzing ? 'Analysing…' : selectedJob.status === 'analyzed' ? 'Re-analyse' : 'Analyse job'}
              </button>
              {selectedJob.status === 'analyzed' && <Link to="/skill-gap" className="btn-primary">Compare with my skills →</Link>}
            </div>
          </div>
          {selectedJob.status === 'analyzed' && (
            <p className="m-0 rounded-xl bg-slate-50 px-3.5 py-2.5 text-sm text-slate-700">
              Re-analyse extracts the requirements again from the saved description. Run Skill Gap afterwards to see the updated result.
            </p>
          )}
          <RequirementsView requirements={selectedJob.requirements} />
        </section>
      ) : (
        jobs.length > 0 && <p className="m-0 text-muted">Select a job description above to see its requirements.</p>
      )}
    </div>
  );
}
