import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AuthShell from '../components/auth/AuthShell';
import { RegisterBridge } from '../components/auth/BridgeIllustration';
import { Field, FormError, SubmitButton, InfoStrip } from '../components/auth/FormBits';

function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [targetRole, setTargetRole] = useState('');
  const [error, setError] = useState('');
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
      await register(name, email, password, targetRole || null);
      navigate('/login');
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else {
        setError('Registration failed. Please check your details and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      illustration={<RegisterBridge />}
      headline={<>Every bridge starts <br className="hidden lg:inline" />with one <span className="text-orange-400">plank</span>.</>}
      subtitle="Create your account, add the skills you already have, and see exactly what stands between you and the role you want."
      cornerText="Already a member?"
      cornerLink="Sign in"
      cornerTo="/login"
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <h2 className="m-0 font-display text-[34px] font-bold tracking-tight">Create your account</h2>
          <p className="mt-2 text-base text-muted">It takes less than a minute to start.</p>
        </div>

        <FormError>{error}</FormError>

        <Field id="name" label="Full name" icon="user" placeholder="Your full name" autoComplete="name"
          value={name} onChange={(e) => setName(e.target.value)} required maxLength={100} />
        <Field id="email" label="Email address" icon="mail" type="email" placeholder="you@example.com" autoComplete="email"
          value={email} onChange={(e) => setEmail(e.target.value)} required />
        <Field id="role" label="Target career role" icon="case" placeholder="e.g. Agentic AI Engineer" hint="Optional"
          value={targetRole} onChange={(e) => setTargetRole(e.target.value)} maxLength={150} />
        <div className="grid gap-3 sm:grid-cols-2">
          <Field id="password" label="Password" type="password" placeholder="8–128 characters" autoComplete="new-password"
            value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} maxLength={128} />
          <Field id="confirm" label="Confirm password" type="password" placeholder="Repeat password" autoComplete="new-password"
            value={confirm} onChange={(e) => setConfirm(e.target.value)} required minLength={8} maxLength={128} />
        </div>

        <SubmitButton loading={loading} loadingText="Creating account...">Create account</SubmitButton>

        <InfoStrip
          title="Your first 3 steps"
          items={[
            { value: '1', label: 'Add your skills', color: 'text-brand' },
            { value: '2', label: 'Paste a job', color: 'text-high' },
            { value: '3', label: 'See your gaps', color: 'text-verified' },
          ]}
        />
      </form>
    </AuthShell>
  );
}

export default Register;
