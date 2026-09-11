export default function SkillList({ profile, onEdit, onDelete }) {
  if (profile.length === 0) {
    return <p className="text-gray-500 italic">No skills yet — add one manually or connect GitHub.</p>;
  }

  return (
    <div className="grid gap-3">
      {profile.map((skill) => (
        <div key={skill.skill_name} className="bg-white p-4 rounded-lg shadow flex justify-between items-center">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-lg">{skill.skill_name}</span>
              <span className="text-xs bg-gray-100 px-2 py-0.5 rounded text-gray-600">{skill.category.replace('_', ' ')}</span>
            </div>
            {skill.self_assessed_level && (
              <p className="text-sm text-gray-600 capitalize">Self-assessed: {skill.self_assessed_level}</p>
            )}
            {skill.demonstrated ? (
              <p className="text-sm text-green-700">✓ Demonstrated on GitHub — found in {skill.evidence_count} repositor{skill.evidence_count === 1 ? 'y' : 'ies'}</p>
            ) : (
              <p className="text-sm text-gray-400">Not yet demonstrated</p>
            )}
          </div>
          {skill.sources.includes('manual') && (
            <div className="flex gap-2">
              <button onClick={() => onEdit(skill)} className="text-blue-600 text-sm hover:underline">Edit</button>
              <button onClick={() => onDelete(skill)} className="text-red-600 text-sm hover:underline">Delete</button>
            </div>
          )}
        </div>
      ))}
    </div>

  );
}