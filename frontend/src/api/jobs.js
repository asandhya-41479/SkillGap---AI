import api from './axios';

export const getJobs = () => api.get('/jobs');
export const getJob = (id) => api.get(`/jobs/${id}`);
export const createJob = (data) => api.post('/jobs', data);
export const deleteJob = (id) => api.delete(`/jobs/${id}`);
export const analyzeJob = (id) => api.post(`/jobs/${id}/analyze`);