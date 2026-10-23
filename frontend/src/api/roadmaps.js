import api from './axios';

// Creating a roadmap waits for the AI service (and its fallbacks), so allow up to 3 minutes.
export const createRoadmap = (body) => api.post('/roadmaps', body, { timeout: 180000 });
// Regenerating waits for the AI service too, so it gets the same long timeout.
export const regenerateRoadmap = (id, body) => api.post(`/roadmaps/${id}/regenerate`, body, { timeout: 180000 });
// Asks the AI service again for better wording on an existing roadmap (same long timeout).
export const improveRoadmap = (id) => api.post(`/roadmaps/${id}/improve`, null, { timeout: 180000 });
export const listRoadmaps = () => api.get('/roadmaps');
export const getRoadmap = (id) => api.get(`/roadmaps/${id}`);
export const setItemStatus = (roadmapId, itemId, status) =>
  api.patch(`/roadmaps/${roadmapId}/items/${itemId}`, { status });
export const deleteRoadmap = (id) => api.delete(`/roadmaps/${id}`);