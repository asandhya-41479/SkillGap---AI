import { useState, useEffect } from 'react';
import { getSkills, addSkill, updateSkill, deleteSkill, getProfile } from '../api/skills';
import { connectGithub, getGithubStatus, analyzeRepos } from '../api/github';
import SkillForm from '../components/skills/SkillForm';
import SkillList from '../components/skills/SkillList';
import GitHubConnectCard from '../components/skills/GitHubConnectCard';

export default function SkillProfile() {
  const [profile, setProfile] = useState([]);
  const [githubStatus, setGithubStatus] = useState(null);
  const [editingSkill, setEditingSkill] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');

  const loadAll = async () => {
    try {
      const [profileRes, statusRes] = await Promise.all([getProfile(), getGithubStatus()]);
      setProfile(profileRes.data);
      setGithubStatus(statusRes.data);
    } catch {
      setError('Failed to load your skill profile.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAll(); }, []);

  const handleAdd = async (data) => {
    try {
      await addSkill(data);
      loadAll();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add skill.');
    }
  };

  const handleUpdate = async (data) => {
    try {
      const raw = await getSkills();
      const target = raw.data.find((s) => s.skill_name === editingSkill.skill_name);
      await updateSkill(target.id, data);
      setEditingSkill(null);
      loadAll();
    } catch {
      setError('Failed to update skill.');
    }
  };

  const handleDelete = async (skill) => {
    const raw = await getSkills();
    const target = raw.data.find((s) => s.skill_name === skill.skill_name);
    await deleteSkill(target.id);
    loadAll();
  };

  const handleConnect = async () => {
    const res = await connectGithub();
    window.location.href = res.data.authorize_url;
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      await analyzeRepos();
      loadAll();
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Loading your skill profile...</div>;

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold">Skill Profile</h1>
      {error && <p className="text-red-600 bg-red-50 p-3 rounded">{error}</p>}

      <GitHubConnectCard status={githubStatus} onConnect={handleConnect} onAnalyze={handleAnalyze} analyzing={analyzing} />

      <SkillForm
        onSubmit={editingSkill ? handleUpdate : handleAdd}
        editingSkill={editingSkill}
        onCancel={() => setEditingSkill(null)}
      />

      <SkillList profile={profile} onEdit={setEditingSkill} onDelete={handleDelete} />
    </div>
  );
}