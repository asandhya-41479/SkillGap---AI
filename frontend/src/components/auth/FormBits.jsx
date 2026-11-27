import { useState } from 'react';

const ICONS = {
  mail: 'M3 5h18v14H3zM3 7l9 6 9-6',
  lock: 'M5 11h14v10H5zM8 11V8a4 4 0 018 0v3',
  user: 'M12 4a4 4 0 100 8 4 4 0 000-8zM4 21c1.5-4 4.5-6 8-6s6.5 2 8 6',
  case: 'M3 7h18v13H3zM8 7V5a2 2 0 012-2h4a2 2 0 012 2v2',
};

// Labelled input with a leading icon; password inputs get a show/hide button.
export function Field({ id, label, icon, type = 'text', hint, ...props }) {
  const [show, setShow] = useState(false);
  const isPassword = type === 'password';
  return (
    <div className="flex min-w-0 flex-col gap-2">
      <div className="flex flex-wrap items-baseline justify-between gap-x-2 gap-y-0.5">
        <label htmlFor={id} className="field-label">{label}</label>
        {hint && <span className="text-xs text-muted">{hint}</span>}
      </div>
      <div className="field-box">
        {icon && (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#475569" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d={ICONS[icon]} />
          </svg>
        )}
        <input id={id} type={isPassword && show ? 'text' : type} {...props} />
        {isPassword && (
          <button type="button" onClick={() => setShow((s) => !s)} aria-label={show ? 'Hide password' : 'Show password'}
            className="-mr-2.5 flex h-11 w-11 items-center justify-center rounded-lg text-slate-600 hover:text-ink">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" />
              {show && <path d="M3 3l18 18" />}
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}

export function FormError({ children }) {
  if (!children) return null;
  return (
    <div role="alert" className="flex gap-2.5 rounded-xl border border-red-200 bg-red-50 px-3.5 py-3 text-sm text-red-800">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mt-px flex-none" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 8v5M12 16h.01" /></svg>
      <span>{children}</span>
    </div>
  );
}

export function SubmitButton({ loading, children, loadingText }) {
  return (
    <button type="submit" disabled={loading} className="btn-primary h-[54px] w-full text-base">
      {loading ? loadingText : children}
      {!loading && (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
      )}
    </button>
  );
}

// "What you'll see inside" / "Your first 3 steps" box.
export function InfoStrip({ title, items }) {
  return (
    <div className="rounded-2xl bg-slate-100 p-4">
      <p className="eyebrow m-0 mb-2.5">{title}</p>
      <div className="grid grid-cols-3 gap-2.5">
        {items.map((it) => (
          <div key={it.label} className="flex min-w-0 flex-col gap-1 rounded-xl border border-line bg-white p-3">
            <b className={`font-display text-lg ${it.color}`}>{it.value}</b>
            <span className="text-xs font-semibold text-muted">{it.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
