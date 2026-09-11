import api from './axios';

export const getSkills = () => api.get('/skills');
export const addSkill = (data) => api.post('/skills', data);
export const updateSkill = (id, data) => api.put(`/skills/${id}`, data);
export const deleteSkill = (id) => api.delete(`/skills/${id}`);
export const getProfile = () => api.get('/profile/skills');