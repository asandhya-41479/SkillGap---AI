import { STATUS, WEIGHT, statusOf, nameOf, importanceOf, symbolOf } from '../../lib/gap';

const TILE = {
  strong: 'bg-[#2563EB] text-white',
  high: 'bg-[#C2410C] text-white',
  medium: 'bg-[#F2B705] text-ink',
  low: 'bg-slate-200 text-ink',
};

// Every requirement of the job as an "element": symbol, name, weight, coloured by status.
export default function PeriodicTable({ results }) {
  return (
    <div>
      <ul className="m-0 grid list-none grid-cols-3 gap-2 p-0 sm:grid-cols-5 lg:grid-cols-7 xl:grid-cols-9">
        {results.map((r) => {
          const st = statusOf(r);
          const w = WEIGHT[importanceOf(r)];
          return (
            <li key={r.id} title={`${nameOf(r)} · ${STATUS[st].label} · weight ${w}`}
              className={`flex aspect-[0.9] min-w-0 flex-col justify-between rounded-lg p-2.5 ${TILE[st]}`}>
              <span className="text-[11px] font-bold opacity-90">×{w}</span>
              <span className="font-display text-[34px] leading-none">{symbolOf(nameOf(r))}</span>
              <span className="truncate text-[11px] font-semibold">{nameOf(r)}</span>
            </li>
          );
        })}
      </ul>
      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-[13px] font-semibold text-slate-700">
        {Object.entries(TILE).map(([k, cls]) => (
          <span key={k} className="flex items-center gap-2"><span className={`h-3.5 w-3.5 rounded ${cls}`} />{STATUS[k].label}</span>
        ))}
        <span className="text-muted">×2 required · ×1 preferred · ×0.5 optional</span>
      </div>
    </div>
  );
}
