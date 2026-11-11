import api from './axios';

// Readiness is calculated on the backend (deterministic formula). The frontend only displays it.
// Calculating may wait for the optional Gemini summary (max ~8 s on the backend), so allow 30 s.
export const calculateReadiness = (analysisId) => api.post(`/readiness/${analysisId}/calculate`, null, { timeout: 30000 });
export const getLatestReadinessForJob = (jobId) => api.get(`/readiness/jobs/${jobId}/latest`);
export const getReadinessHistory = (jobId) => api.get(`/readiness/jobs/${jobId}/history`);
export const compareAnalyses = (fromAnalysisId, toAnalysisId) =>
  api.get('/readiness/compare', { params: { from_analysis_id: fromAnalysisId, to_analysis_id: toAnalysisId } });
