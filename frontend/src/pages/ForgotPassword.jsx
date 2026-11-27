import { useState } from 'react';
import api from '../api/axios';
import AuthShell from '../components/auth/AuthShell';
import { LoginBridge } from '../components/auth/BridgeIllustration';
import { Field, FormError, SubmitButton } from '../components/auth/FormBits';

// Step 1 of a password reset: ask for the email. The answer is the same whether or not the
// account exists, so this page never reveals who is registered.
function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.post('/auth/forgot-password', { email });
      setSent(res.data.detail);
    } catch (err) {
      const d = err.response?.data?.detail;
      setError(typeof d === 'string' ? d : 'Please enter a valid email address.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      illustration={<LoginBridge />}
      headline={<>Lost a plank? <br className="hidden lg:inline" />We&apos;ll help you <span className="text-orange-400">rebuild</span>.</>}
      subtitle="Enter the email you signed up with and we'll send you a secure link to choose a new password."
      cornerText="Remembered it?"
      cornerLink="Sign in"
      cornerTo="/login"
    >
      {sent ? (
        <div className="flex flex-col gap-5">
          <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-green-100 text-green-700" aria-hidden="true">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 5h18v14H3zM3 7l9 6 9-6" /></svg>
          </span>
          <div>
            <h2 className="m-0 font-display text-[34px] font-bold tracking-tight">Check your email</h2>
            <p role="status" className="mt-2 text-base text-muted">{sent}</p>
          </div>
          <ul className="m-0 flex list-disc flex-col gap-1.5 rounded-xl bg-slate-100 py-3.5 pl-8 pr-4 text-sm text-slate-700">
            <li>The link is valid for 30 minutes and works once.</li>
            <li>Can&apos;t find it? Check your spam or promotions folder.</li>
            <li>Asking again cancels the earlier link.</li>
          </ul>
          <button type="button" onClick={() => { setSent(''); }} className="btn-secondary self-start">Use a different email</button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div>
            <h2 className="m-0 font-display text-[34px] font-bold tracking-tight">Forgot your password?</h2>
            <p className="mt-2 text-base text-muted">No problem. We&apos;ll email you a reset link.</p>
          </div>
          <FormError>{error}</FormError>
          <Field id="email" label="Email address" icon="mail" type="email" placeholder="you@example.com"
            autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <SubmitButton loading={loading} loadingText="Sending…">Send reset link</SubmitButton>
        </form>
      )}
    </AuthShell>
  );
}

export default ForgotPassword;
