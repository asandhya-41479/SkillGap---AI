import api from './axios';

// Module 7: Career Action & Opportunity Intelligence. Everything is decided on the backend
// (deterministic engine); the frontend only displays and sends the user's own status changes.
// Generating may wait for the optional Gemini wording (max ~15 s on the backend), so allow 30 s.
const SLOW = { timeout: 30000 };

export const getCareerPlan = (analysisId) => api.get(`/career/${analysisId}/plan`, SLOW);
export const generateCareerPlan = (analysisId, force = false) =>
  api.post(`/career/${analysisId}/plan/generate`, { force }, SLOW);
export const listCareerActions = (params) => api.get('/career/actions', { params });
export const updateCareerAction = (actionId, data) => api.patch(`/career/actions/${actionId}`, data);

export const getInterviewPrep = (analysisId) => api.get(`/career/${analysisId}/interview-prep`, SLOW);
export const generateInterviewPrep = (analysisId, force = false) =>
  api.post(`/career/${analysisId}/interview-prep/generate`, { force }, SLOW);
export const updateInterviewItem = (itemId, status) => api.patch(`/career/interview-prep/${itemId}`, { status });

export const getOpportunitySourceStatus = () => api.get('/career/opportunities/source-status');
export const getSavedJobMatches = () => api.get('/career/opportunities/saved-jobs');
export const matchOpportunity = (data) => api.post('/career/opportunities/match', data);
export const listOpportunityMatches = () => api.get('/career/opportunities');
export const deleteOpportunityMatch = (id) => api.delete(`/career/opportunities/${id}`);
