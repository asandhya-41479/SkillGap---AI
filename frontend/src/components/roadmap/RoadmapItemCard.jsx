import { useState } from 'react';

const PRIORITY = {
  high: 'bg-orange-100 text-orange-800',
  medium: 'bg-amber-100 text-amber-800',
  low: 'bg-slate-100 text-slate-700',
};
const STATUSES = [
  ['not_started', 'Not started'],
  ['in_progress', 'In progress'],
  ['completed', 'Completed'],
  ['skipped', 'Skipped'],
];
const STATUS_RING = {
  completed: 'border-green-300 bg-green-50/40',
  in_progress: 'border-blue-300',
  skipped: 'border-line opacity-70',
  not_started: 'border-line',
};

export default function RoadmapItemCard({ item, onStatus, busy, readOnly = false }) {
  const [open, setOpen] = useState(false);
  const weeks = !item.is_scheduled
    ? ''
    : item.start_week === null
      ? 'Carried over · '
      : `Week${item.start_week === item.end_week ? ` ${item.start_week}` : `s ${item.start_week}–${item.end_week}`} · `;

  return (
    <article className={`flex flex-col gap-2 rounded-2xl border-[1.5px] bg-white p-4 ${STATUS_RING[item.status] || 'border-line'}`}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <h4 className="m-0 font-display text-base font-bold text-ink">
            {item.status === 'completed' && <span className="mr-1.5 text-green-700" aria-hidden="true">✓</span>}
            {item.skill_name}
          </h4>
          <p className="m-0 mt-0.5 text-[13px] text-muted">
            {weeks}≈{item.estimated_hours} h{item.is_supplementary ? ' · supporting skill' : ''}
            {item.reduced_scope ? ' · core topics only' : ''}
          </p>
        </div>
        {item.priority !== 'none' && (
          <span className={`flex-none rounded-full px-2.5 py-1 text-xs font-bold ${PRIORITY[item.priority] || PRIORITY.low}`}>
            {item.priority.charAt(0).toUpperCase() + item.priority.slice(1)} priority
          </span>
        )}
      </div>

      {item.reason && <p className="m-0 text-sm leading-relaxed text-slate-700">{item.reason}</p>}
      {item.prerequisites.length > 0 && (
        <p className="m-0 text-xs font-semibold text-muted">Do first: {item.prerequisites.join(', ')}</p>
      )}

      {item.is_scheduled && (
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <label className="sr-only" htmlFor={`st-${item.id}`}>Status of {item.skill_name}</label>
          <select id={`st-${item.id}`} value={item.status} disabled={busy || readOnly}
            onChange={(e) => onStatus(item, e.target.value)}
            className="h-10 rounded-xl border-[1.5px] border-slate-300 bg-white px-3 text-sm font-semibold text-ink focus:border-brand focus:outline-none focus:ring-4 focus:ring-brand-soft disabled:opacity-60">
            {STATUSES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <button type="button" onClick={() => setOpen(!open)} aria-expanded={open}
            className="min-h-10 rounded-xl px-3 text-sm font-semibold text-brand hover:bg-brand-soft">
            {open ? 'Hide' : 'Show'} study plan
          </button>
          {busy && <span className="text-xs text-muted">Saving…</span>}
        </div>
      )}

      {open && (
        <div className="mt-1 grid gap-3 rounded-xl bg-slate-50 p-3.5 text-sm text-slate-700 sm:grid-cols-2">
          <div>
            <p className="eyebrow m-0 mb-1">Topics</p>
            <ul className="m-0 list-disc space-y-0.5 pl-5">{item.topics.map((t) => <li key={t}>{t}</li>)}</ul>
          </div>
          <div>
            <p className="eyebrow m-0 mb-1">Practice</p>
            <ul className="m-0 list-disc space-y-1 pl-5">
              {item.practical_tasks.map((t) => <li key={t.title}><b>{t.title}:</b> {t.description}</li>)}
            </ul>
          </div>
          {item.project_task && <p className="m-0 sm:col-span-2"><b>Project task:</b> {item.project_task}</p>}
          {item.milestone && <p className="m-0 sm:col-span-2"><b>Milestone:</b> {item.milestone}</p>}
        </div>
      )}
    </article>
  );
}
