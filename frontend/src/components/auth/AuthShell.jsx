import { Link } from 'react-router-dom';
import Logo from '../layout/Logo';

const FEATURES = [
  { label: 'Skill Gap Analysis', bg: 'bg-blue-900', fg: 'text-blue-300', d: 'M11 4a7 7 0 100 14 7 7 0 000-14zM20 20l-4-4' },
  { label: 'Personalised Roadmap', bg: 'bg-orange-950', fg: 'text-orange-300', d: 'M9 4L3 6v14l6-2 6 2 6-2V4l-6 2-6-2z' },
  { label: 'Progress Tracking', bg: 'bg-green-900', fg: 'text-green-300', d: 'M3 17l6-6 4 4 8-8' },
  { label: 'Career Readiness', bg: 'bg-cyan-900', fg: 'text-cyan-300', d: 'M12 3l2.5 5 5.5.8-4 3.9.9 5.5L12 15.6 7.1 18.2l.9-5.5-4-3.9L9.5 8z' },
];

// Two-column auth layout: navy story panel on the left, form on the right.
export default function AuthShell({ illustration, headline, subtitle, cornerText, cornerLink, cornerTo, children }) {
  return (
    <div className="min-h-screen bg-white lg:grid lg:grid-cols-[1.4fr_1fr]">
      <section className="relative flex flex-col gap-3 overflow-hidden bg-night px-6 pb-6 pt-7 text-white lg:min-h-screen lg:px-12 lg:pb-8 lg:pt-9">
        <Logo tagline />
        <div className="mt-1">{illustration}</div>
        <div className="relative z-10 mt-1">
          <h1 className="m-0 font-display text-[32px] font-bold leading-[1.08] tracking-tight lg:text-[44px]">{headline}</h1>
          <p className="mt-3 max-w-xl text-base leading-relaxed text-[#BFD0F0]">{subtitle}</p>
        </div>
        <ul className="relative z-10 mt-auto hidden list-none grid-cols-4 gap-2.5 p-0 pt-4 lg:grid">
          {FEATURES.map((f) => (
            <li key={f.label} className="flex items-center gap-2.5 rounded-2xl border border-[#1E3366] bg-[#0E1B3D] px-3.5 py-3 text-[13px] font-semibold text-[#DCE6FA]">
              <span className={`flex h-8 w-8 flex-none items-center justify-center rounded-lg ${f.bg} ${f.fg}`}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden="true"><path d={f.d} /></svg>
              </span>
              {f.label}
            </li>
          ))}
        </ul>
      </section>

      <section className="relative flex flex-col items-stretch px-5 pb-10 pt-5 lg:flex-row lg:items-center lg:justify-center lg:px-10 lg:pb-12 lg:pt-16">
        <div aria-hidden="true" className="pointer-events-none absolute right-0 top-0 h-64 w-64 bg-[radial-gradient(#DBEAFE_1.2px,transparent_1.2px)] [background-size:18px_18px] [mask-image:linear-gradient(225deg,#000,transparent_70%)]" />
        <p className="relative z-10 m-0 mb-5 self-end text-sm text-muted lg:absolute lg:right-10 lg:top-6 lg:mb-0">
          {cornerText} <Link to={cornerTo} className="font-bold text-brand hover:text-brand-dark hover:underline">{cornerLink}</Link>
        </p>
        <div className="relative z-10 mx-auto w-full max-w-[420px]">{children}</div>
      </section>
    </div>
  );
}
