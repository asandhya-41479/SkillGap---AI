const GROUPS = [
  { key: 'required', title: 'Required', weight: '×2', chip: 'bg-blue-50 text-blue-900 ring-blue-200', head: 'text-brand-dark' },
  { key: 'preferred', title: 'Preferred', weight: '×1', chip: 'bg-amber-50 text-amber-900 ring-amber-200', head: 'text-amber-800' },
  { key: 'optional', title: 'Optional', weight: '×0.5', chip: 'bg-slate-100 text-slate-800 ring-slate-200', head: 'text-slate-700' },
];

// Extracted requirements grouped by importance; "any one of" alternatives shown under the chip.
export default function RequirementsView({ requirements }) {
  if (!requirements || requirements.length === 0) {
    return <p className="m-0 text-muted">No requirements extracted yet. Click Analyse to extract them.</p>;
  }

  return (
    <div className="flex flex-col gap-5">
      {GROUPS.map((g) => {
        const items = requirements.filter((r) => r.importance === g.key);
        if (items.length === 0) return null;
        return (
          <div key={g.key}>
            <h4 className={`m-0 mb-2 flex items-center gap-2 text-sm font-bold uppercase tracking-wider ${g.head}`}>
              {g.title} <span className="rounded-full bg-white px-2 py-0.5 text-xs ring-1 ring-line">{items.length} · weight {g.weight}</span>
            </h4>
            <ul className="m-0 flex list-none flex-wrap gap-2 p-0">
              {items.map((r) => (
                <li key={r.skill_name} className={`rounded-xl px-3 py-1.5 text-sm font-semibold ring-1 ${g.chip}`} title={r.category?.replace('_', ' ')}>
                  {r.skill_name}
                  {r.alternatives?.length > 0 && (
                    <span className="block text-xs font-normal opacity-90">Any one of: {r.alternatives.join(', ')}</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </div>
  );
}
