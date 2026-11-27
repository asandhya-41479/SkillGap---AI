import { useEffect, useState } from 'react';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import { Field, FormError } from '../components/auth/FormBits';
import { connectGithub, getGithubStatus } from '../api/github';

// Suggestions only: the target role stays free text.
const ROLE_SUGGESTIONS = ['Agentic AI Engineer', 'AI Engineer', 'Machine Learning Engineer', 'Data Scientist', 'Data Analyst',
  'Backend Developer', 'Full Stack Developer', 'Frontend Developer', 'DevOps Engineer', 'Cloud Engineer'];

// Profile details (PUT /users/me) and password change (PUT /users/me/password).
function Settings() {
  const { user, fetchCurrentUser } = useAuth();

  const [name, setName] = useState('');
  const [targetRole, setTargetRole] = useState('');
  const [profileMsg, setProfileMsg] = useState('');
  const [profileErr, setProfileErr] = useState('');
  const [savingProfile, setSavingProfile] = useState(false);

  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [pwMsg, setPwMsg] = useState('');
  const [pwErr, setPwErr] = useState('');
  const [savingPw, setSavingPw] = useState(false);

  const [github, setGithub] = useState(null);
  useEffect(() => { getGithubStatus().then((r) => setGithub(r.data)).catch(() => {}); }, []);
  const reconnect = async () => {
    const res = await connectGithub();
    window.location.href = res.data.authorize_url;
  };

  useEffect(() => {
    if (user) {
      setName(user.name || '');
      setTargetRole(user.target_role || '');
    }
  }, [user]);

  const detailOf = (err, fallback) => {
    const d = err.response?.data?.detail;
    if (typeof d === 'string') return d;
    if (Array.isArray(d) && d[0]?.msg) return d[0].msg.replace(/^Value error, /, '');
    return fallback;
  };

  const saveProfile = async (e) => {
    e.preventDefault();
    setProfileMsg(''); setProfileErr(''); setSavingProfile(true);
    try {
      await api.put('/users/me', { name: name.trim(), target_role: targetRole.trim() || null });
      await fetchCurrentUser();
      setProfileMsg('Profile saved.');
    } catch (err) {
      setProfileErr(detailOf(err, 'Could not save your profile. Please try again.'));
    } finally {
      setSavingProfile(false);
    }
  };

  const changePassword = async (e) => {
    e.preventDefault();
    setPwMsg(''); setPwErr('');
    if (next !== confirm) { setPwErr('The new passwords do not match.'); return; }
    setSavingPw(true);
    try {
      await api.put('/users/me/password', { current_password: current, new_password: next });
      setCurrent(''); setNext(''); setConfirm('');
      setPwMsg('Password updated.');
    } catch (err) {
      setPwErr(detailOf(err, 'Could not update your password. Please try again.'));
    } finally {
      setSavingPw(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="eyebrow m-0">Settings</p>
        <h1 className="page-title mt-1">Account settings</h1>
        <p className="mt-1 text-muted">Manage your profile and keep your account secure.</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <form onSubmit={saveProfile} className="card flex flex-col gap-4">
          <h2 className="m-0 font-display text-xl font-bold">Profile details</h2>
          <FormError>{profileErr}</FormError>
          {profileMsg && <p role="status" className="m-0 rounded-xl bg-green-50 px-3.5 py-2.5 text-sm font-semibold text-green-800">{profileMsg}</p>}
          <Field id="s-name" label="Full name" icon="user" value={name} onChange={(e) => setName(e.target.value)} required maxLength={100} />
          <div className="flex flex-col gap-2">
            <span className="field-label">Email address</span>
            <p className="m-0 flex h-13 items-center rounded-xl bg-slate-100 px-3.5 text-[15px] text-muted">{user?.email || '—'}</p>
          </div>
          <Field id="s-role" label="Target career role" icon="case" value={targetRole} onChange={(e) => setTargetRole(e.target.value)} maxLength={150}
            placeholder="Type or pick a role" list="role-suggestions" hint="Type your own or pick one" />
          <datalist id="role-suggestions">{ROLE_SUGGESTIONS.map((r) => <option key={r} value={r} />)}</datalist>
          <button type="submit" className="btn-primary self-start" disabled={savingProfile}>{savingProfile ? 'Saving...' : 'Save changes'}</button>
          <div className="mt-2 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-4">
            <div>
              <p className="m-0 font-semibold text-ink">GitHub</p>
              <p className="m-0 text-sm text-muted">
                {github?.connected ? <>Connected as <b className="text-ink">{github.github_username}</b></> : 'Not connected'}
              </p>
            </div>
            <button type="button" onClick={reconnect} className="btn-secondary">{github?.connected ? 'Reconnect GitHub' : 'Connect GitHub'}</button>
          </div>
        </form>

        <form onSubmit={changePassword} className="card flex flex-col gap-4">
          <h2 className="m-0 font-display text-xl font-bold">Change password</h2>
          <FormError>{pwErr}</FormError>
          {pwMsg && <p role="status" className="m-0 rounded-xl bg-green-50 px-3.5 py-2.5 text-sm font-semibold text-green-800">{pwMsg}</p>}
          <Field id="s-cur" label="Current password" icon="lock" type="password" autoComplete="current-password"
            value={current} onChange={(e) => setCurrent(e.target.value)} required maxLength={128} />
          <Field id="s-new" label="New password" icon="lock" type="password" autoComplete="new-password" hint="8–128 characters"
            value={next} onChange={(e) => setNext(e.target.value)} required minLength={8} maxLength={128} />
          <Field id="s-conf" label="Confirm new password" icon="lock" type="password" autoComplete="new-password"
            value={confirm} onChange={(e) => setConfirm(e.target.value)} required minLength={8} maxLength={128} />
          <p className="m-0 text-sm text-muted">Your new password must be different from your current one.</p>
          <button type="submit" className="btn-primary self-start" disabled={savingPw}>{savingPw ? 'Updating...' : 'Update password'}</button>
        </form>
      </div>
    </div>
  );
}

export default Settings;
