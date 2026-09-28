import api from './axios';

export const runGapAnalysis = (jobId) => api.post(`/gap-analysis/${jobId}`);
export const listAnalyses = () => api.get('/gap-analysis');
export const getAnalysis = (id) => api.get(`/gap-analysis/${id}`);
export const getAnalysisResults = (id) => api.get(`/gap-analysis/${id}/results`);