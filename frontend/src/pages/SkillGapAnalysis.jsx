import { useState, useEffect } from 'react';
import { getJobs } from '../api/jobs';
import { runGapAnalysis } from '../api/skillGap';
import ResultRow from '../components/skillgap/ResultRow';

const SECTIONS = [
  { key: 'strong', title: 'Strong Matches' },
  { key: 'partial', title: 'Partial Matches' },
  { key: 'transferable', title: 'Transferable' },
  { key: 'gap', title: 'Skill Gaps' },
];

export default function SkillGapAnalysis() {
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysis, setAnalysis] = useState(null);

  useEffect(() => {
    getJobs().then((res) => setJobs(res.data)).catch(() => setError('Could not load jobs.'));
  }, []);

  const handleRun = async () => {
    if (!selectedJobId) return;
    setLoading(true);
    setError('');
    setAnalysis(null);
    try {
      const res = await runGapAnalysis(selectedJobId);
      setAnalysis(res.data);
    } catch (err) {

      setError(err.response?.data?.detail || 'Analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 720, margin: '0 auto', padding: 24 }}>
      <h1>Skill Gap Analysis</h1>

      <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        <select value={selectedJobId} onChange={(e) => setSelectedJobId(e.target.value)} style={{ flex: 1, padding: 8 }}>
          <option value="">Select a job…</option>
          {jobs.map((job) => (
            <option key={job.id} value={job.id}>
              {job.title || job.target_role} (#{job.id})
            </option>
          ))}
        </select>
        <button onClick={handleRun} disabled={!selectedJobId || loading}>
          {loading ? 'Analyzing…' : 'Run Analysis'}
        </button>
      </div>

      {error && <p style={{ color: '#d92d20' }}>{error}</p>}

      {analysis && (
        <>
          <div style={{ textAlign: 'center', margin: '24px 0' }}>
            <div style={{ fontSize: 14, color: '#667085' }}>SKILL ALIGNMENT</div>
            <div style={{ fontSize: 48, fontWeight: 700 }}>
              {analysis.overall_alignment_score ?? '—'}%

            </div>
            <div style={{ fontSize: 12, color: '#667085' }}>
              Measures how closely your skills map to this role's requirements — not a hiring probability.
            </div>
          </div>

          {SECTIONS.map(({ key, title }) => {
            const items = analysis.results.filter((r) => r.classification === key);
            if (items.length === 0) return null;
            return (
              <div key={key} style={{ marginBottom: 20 }}>
                <h3>{title}</h3>
                {items.map((result) => (
                  <ResultRow
                    key={result.id}
                    result={result}
                    requirement={
                      result.job_requirement || {
                        skill_name: `Requirement #${result.job_requirement_id}`,
                        importance: '',
                      }
                    }
                  />
                ))}
              </div>
            );
          })}
        </>
      )}
    </div>
  );
}