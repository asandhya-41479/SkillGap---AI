import { useState, useEffect } from 'react';
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

  useEffect(() => { loadJobs(); }, []);

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

  if (loading) return <div className="p-8 text-center text-gray-500">Loading job intelligence...</div>;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold">Job Market Intelligence</h1>
      {error && <p className="text-red-600 bg-red-50 p-3 rounded">{error}</p>}

      <JobForm onSubmit={handleCreate} submitting={submitting} />

      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <h2 className="text-lg font-semibold mb-2">Your Job Descriptions</h2>
          <JobList jobs={jobs} selectedId={selectedJob?.id} onSelect={handleSelect} onDelete={handleDelete} />
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-2">Analysis</h2>
          {selectedJob ? (
            <div className="bg-white p-4 rounded-lg shadow space-y-3">
              <div>
                <p className="font-medium">{selectedJob.title || selectedJob.target_role}</p>
                <p className="text-sm text-gray-500">{selectedJob.target_role} — {selectedJob.status}</p>
              </div>
              {selectedJob.status !== 'analyzed' && (
                <button
                  onClick={handleAnalyze}
                  disabled={analyzing}
                  className="bg-gray-800 text-white px-4 py-2 rounded hover:bg-gray-900 disabled:opacity-50"
                >
                  {analyzing ? 'Analyzing...' : 'Analyze'}
                </button>
              )}
              <RequirementsView requirements={selectedJob.requirements} />
            </div>
          ) : (
            <p className="text-gray-500 italic">Select a job description to view its analysis.</p>
          )}
        </div>
      </div>
    </div>
  );
}