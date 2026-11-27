import { CAREER_STATUS, criterionTarget, criterionValue } from './labels';

// Career status + readiness + "what is missing for the next level". All values come from the backend
// (approved rules in career_config.py); nothing is calculated here.

const STAGES = ['BUILDING_FOUNDATION', 'DEVELOPING', 'NEAR_READY', 'READY_TO_APPLY'];

function Criterion({ c }) {
  return (
    <li className="flex items-start gap-2.5 rounded-xl bg-slate-50 px-3 py-2.5 text-sm">
      <span className={`flex h-5 w-5 flex-none items-center justify-center rounded-full text-xs font-bold text-white ${c.met ? 'bg-verified' : 'bg-high'}`} aria-label={c.met ? 'met' : 'not met'}>{c.met ? '✓' : '✗'}</span>
      <span className="flex-1 font-semibold text-ink">{c.label}</span>
      <span className="text-slate-700 whitespace-nowrap">
        {criterionValue(c)} <span className="text-slate-500">(needs {criterionTarget(c)})</span>
      </span>
    </li>
  );
}

export default function StatusCard({ plan }) {
  const st = CAREER_STATUS[plan.career_status] || CAREER_STATUS.BUILDING_FOUNDATION;
  const next = plan.next_status;
  const nextText = next ? (CAREER_STATUS[next.status]?.text || next.status) : null;

  const idx = Math.max(STAGES.indexOf(plan.career_status), 0);

  return (
    <section className="card flex flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="eyebrow m-0">Career status</p>
          <p className="m-0 mt-1 text-sm text-muted">
            Target <b className="text-ink">{plan.target_role}</b> · Readiness{' '}
            <b className="text-ink">{plan.readiness_score === null ? 'not enough data' : `${Math.round(plan.readiness_score)}/100`}</b>
            {plan.readiness_label && plan.readiness_score !== null && <> ({plan.readiness_label})</>}
          </p>
        </div>
        <span className={`rounded-full border px-4 py-1.5 font-display text-lg font-bold ${st.cls}`}>{st.text}</span>
      </div>

      <ol className="m-0 grid list-none grid-cols-2 gap-2 p-0 md:grid-cols-4" aria-label="Career stages">
        {STAGES.map((k, i) => {
          const here = i === idx, done = i < idx;
          return (
            <li key={k} aria-current={here ? 'step' : undefined}
              className={`flex flex-col gap-1 rounded-2xl p-3.5 ${here ? 'bg-brand text-white shadow-[0_8px_20px_rgba(37,99,235,.3)]' : done ? 'bg-green-50 text-green-900' : 'bg-slate-50 text-slate-700'}`}>
              <span className="text-xs font-bold uppercase tracking-wider opacity-90">{here ? 'You are here' : done ? 'Passed' : `Stage ${i + 1}`}</span>
              <span className="font-display text-base font-bold">{i + 1}. {CAREER_STATUS[k].text}</span>
            </li>
          );
        })}
      </ol>

      {next ? (
        <div>
          <h3 className="m-0 mb-2 font-display text-base font-bold">
            Toward {nextText}: {next.met} of {next.total} criteria met
          </h3>
          <ul className="m-0 grid list-none gap-2 p-0 md:grid-cols-2">{next.criteria.map((c) => <Criterion key={c.key} c={c} />)}</ul>
        </div>
      ) : (
        <p className="m-0 rounded-xl bg-green-50 px-3.5 py-2.5 text-sm font-semibold text-green-800">All Ready to Apply criteria are met for this role.</p>
      )}

      <details>
        <summary className="cursor-pointer text-sm font-semibold text-brand">All Ready to Apply criteria</summary>
        <ul className="m-0 mt-2 grid list-none gap-2 p-0 md:grid-cols-2">{plan.status_criteria.map((c) => <Criterion key={c.key} c={c} />)}</ul>
      </details>
      <p className="m-0 text-xs text-muted">{plan.disclaimer}</p>
    </section>
  );
}
