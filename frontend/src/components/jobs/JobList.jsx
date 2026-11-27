const STATUS_STYLE = {
  pending: 'bg-slate-100 text-slate-700',
  analyzed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};
const STATUS_LABEL = { pending: 'Not analysed', analyzed: 'Analysed', failed: 'Failed' };

export default function JobList({ jobs, selectedId, onSelect, onDelete }) {
  if (jobs.length === 0) {
    return <p className="m-0 text-muted">No job descriptions yet. Paste one to get started.</p>;
  }

  return (
    <ul className="m-0 flex list-none flex-col gap-2 p-0">
      {jobs.map((job) => {
        const active = selectedId === job.id;
        return (
          <li key={job.id} className={`flex items-center gap-2 rounded-xl border-[1.5px] transition ${active ? 'border-brand bg-blue-50' : 'border-line bg-white hover:bg-slate-50'}`}>
            <button type="button" onClick={() => onSelect(job.id)} aria-pressed={active}
              className="flex min-h-14 min-w-0 flex-1 flex-col items-start justify-center px-3.5 py-2 text-left">
              <span className="truncate font-semibold text-ink">{job.title || job.target_role}</span>
              <span className="truncate text-sm text-muted">{job.target_role}</span>
            </button>
            <span className={`flex-none rounded-full px-2.5 py-1 text-xs font-bold ${STATUS_STYLE[job.status] || STATUS_STYLE.pending}`}>{STATUS_LABEL[job.status] || job.status}</span>
            <button type="button" onClick={() => onDelete(job.id)} aria-label={`Delete ${job.title || job.target_role}`}
              className="mr-2 flex h-9 w-9 flex-none items-center justify-center rounded-lg text-red-700 hover:bg-red-50">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13" /></svg>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
