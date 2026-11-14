import { CAREER_STATUS, criterionTarget, criterionValue } from './labels';

// Career status + readiness + "what is missing for the next level". All values come from the backend
// (approved rules in career_config.py); nothing is calculated here.

function Criterion({ c }) {
  return (
    <li className="flex items-start gap-2 text-sm">
      <span className={c.met ? 'text-green-600' : 'text-red-500'}>{c.met ? '✓' : '✗'}</span>
      <span className="flex-1">{c.label}</span>
      <span className="text-gray-600 whitespace-nowrap">
        {criterionValue(c)} <span className="text-gray-400">(needs {criterionTarget(c)})</span>
      </span>
    </li>
  );
}

export default function StatusCard({ plan }) {
  const st = CAREER_STATUS[plan.career_status] || CAREER_STATUS.BUILDING_FOUNDATION;
  const next = plan.next_status;
  const nextText = next ? (CAREER_STATUS[next.status]?.text || next.status) : null;

  return (
    <div className="bg-white border rounded-lg p-4 mb-4">
      <div className="text-xs font-semibold tracking-wide text-gray-500">CAREER STATUS</div>
      <div className="flex flex-wrap items-center gap-4 mt-2">
        <span className={`text-xl font-bold px-3 py-1 rounded border ${st.cls}`}>{st.text.toUpperCase()}</span>
        <div className="text-sm">
          <div><span className="text-gray-500">Target:</span> <b>{plan.target_role}</b></div>
          <div>
            <span className="text-gray-500">Readiness:</span>{' '}
            <b>{plan.readiness_score === null ? 'Not enough data' : `${Math.round(plan.readiness_score)} / 100`}</b>
            {plan.readiness_label && plan.readiness_score !== null && (
              <span className="text-gray-500"> ({plan.readiness_label})</span>
            )}
          </div>
        </div>
      </div>

      {next ? (
        <div className="mt-4">
          <div className="text-sm font-medium mb-1">
            Toward <b>{nextText}</b>: {next.met} of {next.total} criteria met
          </div>
          <ul className="space-y-1">{next.criteria.map((c) => <Criterion key={c.key} c={c} />)}</ul>
        </div>
      ) : (
        <p className="mt-3 text-sm text-green-700">All Ready to Apply criteria are met for this role.</p>
      )}

      <details className="mt-3">
        <summary className="text-xs text-purple-700 cursor-pointer">All Ready to Apply criteria</summary>
        <ul className="space-y-1 mt-2">{plan.status_criteria.map((c) => <Criterion key={c.key} c={c} />)}</ul>
      </details>
      <p className="mt-3 text-xs text-gray-500">{plan.disclaimer}</p>
    </div>
  );
}
