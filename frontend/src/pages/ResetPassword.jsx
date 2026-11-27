import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import AuthShell from '../components/auth/AuthShell';
import { LoginBridge } from '../components/auth/BridgeIllustration';
import { Field, FormError, SubmitButton } from '../components/auth/FormBits';

// Step 2 of a password reset: the link in the email opens /reset-password?token=...
function ResetPassword() {
  const navigate = useNavigate();
  const [token] = useState(() => new URLSearchParams(window.location.search).get('token') || '');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (password !== confirm) {
      setError('The two passwords do not match.');
      return;
    }
    setLoading(true);
    try {
      await api.post('/auth/reset-password', { token, new_password: password });
      setDone(true);
      setTimeout(() => navigate('/login'), 2500);
    } catch (err) {
      const d = err.response?.data?.detail;
      setError(typeof d === 'string' ? d : Array.isArray(d) ? 'Your password must be 8 to 128 characters.' : 'Could not reset your password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      illustration={<LoginBridge />}
      headline={<>Set a new password, <br className="hidden lg:inline" />then keep <span className="text-orange-400">building</span>.</>}
      subtitle="Choose a strong password you don't use anywhere else."
      cornerText="Remembered it?"
      cornerLink="Sign in"
      cornerTo="/login"
    >
      {!token ? (
        <div className="flex flex-col gap-4">
          <h2 className="m-0 font-display text-[34px] font-bold tracking-tight">Link not complete</h2>
          <p className="m-0 text-muted">This page needs the full link from your email. Please open the link again, or request a new one.</p>
          <Link to="/forgot-password" className="btn-primary self-start">Request a new link</Link>
        </div>
      ) : done ? (
        <div role="status" className="flex flex-col gap-4">
          <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-green-100 text-2xl font-bold text-green-700" aria-hidden="true">✓</span>
          <h2 className="m-0 font-display text-[34px] font-bold tracking-tight">Password updated</h2>
          <p className="m-0 text-muted">You can now sign in with your new password. Taking you to sign in…</p>
          <Link to="/login" className="btn-primary self-start">Sign in now</Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div>
            <h2 className="m-0 font-display text-[34px] font-bold tracking-tight">Choose a new password</h2>
            <p className="mt-2 text-base text-muted">8 to 128 characters.</p>
          </div>
          {error && (
            <FormError>
              {error}
              {error.includes('expired') && <> <Link to="/forgot-password" className="font-bold underline">Request a new link</Link></>}
            </FormError>
          )}
          <Field id="np" label="New password" icon="lock" type="password" autoComplete="new-password"
            value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} maxLength={128} />
          <Field id="cp" label="Confirm new password" icon="lock" type="password" autoComplete="new-password"
            value={confirm} onChange={(e) => setConfirm(e.target.value)} required minLength={8} maxLength={128} />
          <SubmitButton loading={loading} loadingText="Saving…">Save new password</SubmitButton>
        </form>
      )}
    </AuthShell>
  );
}

export default ResetPassword;
