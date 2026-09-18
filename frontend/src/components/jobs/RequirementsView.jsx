const IMPORTANCE_ORDER = ['required', 'preferred', 'optional'];
const IMPORTANCE_STYLE = {
  required: 'bg-red-50 text-red-700 border-red-200',
  preferred: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  optional: 'bg-gray-50 text-gray-600 border-gray-200',
};

export default function RequirementsView({ requirements }) {
  if (!requirements || requirements.length === 0) {
    return <p className="text-gray-500 italic">No requirements extracted yet.</p>;
  }

  return (
    <div className="space-y-4">
      {IMPORTANCE_ORDER.map((level) => {
        const items = requirements.filter((r) => r.importance === level);
        if (items.length === 0) return null;
        return (
          <div key={level}>
            <h4 className="text-sm font-semibold uppercase text-gray-500 mb-2">{level}</h4>
            <div className="flex flex-wrap gap-2">
              {items.map((r) => (
                <span
                  key={r.skill_name}
                  className={`px-3 py-1 rounded-full border text-sm ${IMPORTANCE_STYLE[level]}`}
                  title={r.category.replace('_', ' ')}
                >
                  {r.skill_name}
                </span>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}