const STATUS_STYLE = {
  pending: 'bg-gray-100 text-gray-600',
  analyzed: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
};

export default function JobList({ jobs, selectedId, onSelect, onDelete }) {
  if (jobs.length === 0) {
    return <p className="text-gray-500 italic">No job descriptions yet — paste one to get started.</p>;
  }

  return (
    <div className="space-y-2">
      {jobs.map((job) => (
        <div
          key={job.id}
          onClick={() => onSelect(job.id)}
          className={`p-3 rounded-lg border cursor-pointer flex justify-between items-center ${
            selectedId === job.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white hover:bg-gray-50'
          }`}
        >
          <div>
            <p className="font-medium">{job.title || job.target_role}</p>
            <p className="text-sm text-gray-500">{job.target_role}</p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-xs px-2 py-1 rounded ${STATUS_STYLE[job.status]}`}>{job.status}</span>
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(job.id); }}
              className="text-red-600 text-sm hover:underline"
            >
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}