import api from './axios';

export const connectGithub = () => api.get('/github/connect');
export const getGithubStatus = () => api.get('/github/status');
export const analyzeRepos = () => api.post('/github/analyze');