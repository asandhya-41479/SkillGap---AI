import { useState, useEffect } from 'react';
import { getSkills, addSkill, updateSkill, deleteSkill, getProfile } from '../api/skills';
import { connectGithub, getGithubStatus, analyzeRepos } from '../api/github';
import SkillForm from '../components/skills/SkillForm';
import SkillList from '../components/skills/SkillList';
import GitHubConnectCard from '../components/skills/GithubConnectCard';

export default function SkillProfile() {
  const [profile, setProfile] = useState([]);
  const [githubStatus, setGithubStatus] = useState(null);
  const [editingSkill, setEditingSkill] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');
  // Set by the backend's GitHub callback: /skills?github=connected or ?github=error
  const [githubNotice] = useState(() => new URLSearchParams(window.location.search).get('github'));

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

  useEffect(() => {
    loadAll();
    if (githubNotice) window.history.replaceState(null, '', window.location.pathname);
  }, []);

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
    if (!window.confirm(`Delete "${skill.skill_name}" from your skills?`)) return;
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

  // Languages detected from GitHub (shown on the GitHub card).
  const languages = profile
    .filter((sk) => sk.sources.includes('github') && sk.category === 'programming_language')
    .map((sk) => sk.skill_name);
  const demonstrated = profile.filter((sk) => sk.demonstrated).length;

  if (loading) return <p className="text-muted">Loading your skill profile…</p>;

  return (
    <div className="flex min-w-0 flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow m-0">My Skills</p>
          <h1 className="page-title mt-1">Your skill profile</h1>
          <p className="mt-1 text-muted">Skills you declare, plus the ones your GitHub repositories prove.</p>
        </div>
        <div className="flex gap-3">
          <div className="rounded-2xl bg-white px-4 py-2.5 text-center shadow-sm"><b className="block font-display text-2xl">{profile.length}</b><span className="text-xs font-semibold text-muted">skills</span></div>
          <div className="rounded-2xl bg-white px-4 py-2.5 text-center shadow-sm"><b className="block font-display text-2xl text-verified">{demonstrated}</b><span className="text-xs font-semibold text-muted">demonstrated</span></div>
        </div>
      </div>

      {error && <p role="alert" className="m-0 rounded-xl bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">{error}</p>}
      {githubNotice === 'connected' && (
        <p role="status" className="m-0 rounded-xl bg-green-50 px-4 py-3 text-sm font-semibold text-green-800">GitHub connected successfully.</p>
      )}
      {githubNotice === 'error' && (
        <p role="alert" className="m-0 rounded-xl bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">GitHub connection did not complete. Please click Connect GitHub and try again.</p>
      )}

      <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
        <SkillForm
          onSubmit={editingSkill ? handleUpdate : handleAdd}
          editingSkill={editingSkill}
          onCancel={() => setEditingSkill(null)}
        />
        <GitHubConnectCard status={githubStatus} onConnect={handleConnect} onAnalyze={handleAnalyze} analyzing={analyzing} languages={languages} />
      </div>

      <SkillList profile={profile} onEdit={setEditingSkill} onDelete={handleDelete} />
    </div>
  );
}
