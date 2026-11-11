import api from './axios';

// GitHub checks run on the backend with the user's stored token, so allow a little longer.
export const listEvidence = () => api.get('/evidence');
export const addEvidence = (body) => api.post('/evidence', body, { timeout: 30000 });
export const verifyEvidence = (id) => api.post(`/evidence/${id}/verify`, null, { timeout: 30000 });
export const deleteEvidence = (id) => api.delete(`/evidence/${id}`);
