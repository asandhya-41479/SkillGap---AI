import { useState } from 'react';

const PRIORITY_COLOR = { high: 'text-red-600', medium: 'text-amber-700', low: 'text-gray-500', none: 'text-gray-500' };
const STATUSES = [
  ['not_started', 'Not started'],
  ['in_progress', 'In progress'],
  ['completed', 'Completed'],
  ['skipped', 'Skipped'],
];

export default function RoadmapItemCard({ item, onStatus, busy, readOnly = false }) {
  const [open, setOpen] = useState(false);
  const weeks = !item.is_scheduled
    ? ''
    : item.start_week === null
      ? 'Carried over · '
      : `Week${item.start_week === item.end_week ? ` ${item.start_week}` : `s ${item.start_week}–${item.end_week}`} · `;

  return (
    <div className={`border rounded-lg p-4 mb-2 bg-white ${item.status === 'completed' ? 'border-green-300' : 'border-gray-200'}`}>
      <div className="flex justify-between items-start gap-3">
        <div>
          <strong>{item.skill_name}</strong>
          <span className="ml-2 text-sm text-gray-500">
            {weeks}≈{item.estimated_hours} h{item.is_supplementary ? ' · supporting skill' : ''}
            {item.reduced_scope ? ' · core topics only' : ''}
          </span>
        </div>
        {item.priority !== 'none' && (
          <span className={`text-xs font-semibold whitespace-nowrap ${PRIORITY_COLOR[item.priority]}`}>
            {item.priority.toUpperCase()} PRIORITY
          </span>

        )}
      </div>

      {item.reason && <p className="mt-2 text-sm text-gray-700">{item.reason}</p>}
      {item.prerequisites.length > 0 && (
        <p className="mt-1 text-xs text-gray-500">Do first: {item.prerequisites.join(', ')}</p>
      )}

      {item.is_scheduled && (
        <div className="mt-3 flex items-center gap-3">
          <select
            value={item.status}
            disabled={busy || readOnly}
            onChange={(e) => onStatus(item, e.target.value)}
            className="border rounded px-2 py-1 text-sm"
          >
            {STATUSES.map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
          <button onClick={() => setOpen(!open)} className="text-xs text-gray-500 hover:underline">
            {open ? 'Hide' : 'Show'} study plan
          </button>
        </div>
      )}

      {open && (
        <div className="mt-3 text-sm text-gray-700 space-y-2">
          <div>
            <strong>Topics</strong>
            <ul className="list-disc ml-5">{item.topics.map((t) => <li key={t}>{t}</li>)}</ul>
          </div>

          <div>
            <strong>Practice</strong>
            <ul className="list-disc ml-5">
              {item.practical_tasks.map((t) => <li key={t.title}><b>{t.title}:</b> {t.description}</li>)}
            </ul>
          </div>
          {item.project_task && <p><strong>Project task:</strong> {item.project_task}</p>}
          {item.milestone && <p><strong>Milestone:</strong> {item.milestone}</p>}
        </div>
      )}
    </div>
  );
}