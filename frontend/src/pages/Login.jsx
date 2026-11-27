import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AuthShell from '../components/auth/AuthShell';
import { LoginBridge } from '../components/auth/BridgeIllustration';
import { Field, FormError, SubmitButton, InfoStrip } from '../components/auth/FormBits';

function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password, remember);
      navigate('/dashboard');
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else {
        setError('Sign-in failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      illustration={<LoginBridge />}
      headline={<>Build the <span className="text-orange-400">bridge</span> to <br className="hidden lg:inline" />your next role.</>}
      subtitle="Every skill you prove adds a plank. SkillGap AI shows you which ones are missing and how to put them in place."
      cornerText="New here?"
      cornerLink="Create account"
      cornerTo="/register"
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-5" noValidate={false}>
        <div>
          <h2 className="m-0 font-display text-[34px] font-bold tracking-tight">Welcome back</h2>
          <p className="mt-2 text-base text-muted">Your next plank is waiting.</p>
        </div>

        <FormError>{error}</FormError>

        <Field id="email" label="Email address" icon="mail" type="email" placeholder="you@example.com"
          autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <Field id="password" label="Password" icon="lock" type="password" placeholder="Enter your password"
          autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />

        <div className="flex flex-wrap items-center justify-between gap-2">
        <label className="flex min-h-11 cursor-pointer items-center gap-2.5 text-sm text-slate-700">
          <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)}
            className="h-[18px] w-[18px] accent-brand" />
          Remember me on this device
        </label>
        <Link to="/forgot-password" className="text-sm font-semibold text-brand hover:text-brand-dark hover:underline">Forgot password?</Link>
        </div>

        <SubmitButton loading={loading} loadingText="Signing in...">Sign in</SubmitButton>

        <div className="flex gap-2.5 rounded-xl bg-slate-100 px-3.5 py-3 text-[13px] leading-relaxed text-muted">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mt-0.5 flex-none" aria-hidden="true"><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z" /></svg>
          <span>For your security, sign-in is paused for 15 minutes after five unsuccessful attempts.</span>
        </div>

        <InfoStrip
          title="What you'll see inside"
          items={[
            { value: '%', label: 'Job alignment', color: 'text-brand' },
            { value: 'Gaps', label: 'Ranked by priority', color: 'text-high' },
            { value: '✓', label: 'GitHub-verified skills', color: 'text-verified' },
          ]}
        />
      </form>
    </AuthShell>
  );
}

export default Login;
