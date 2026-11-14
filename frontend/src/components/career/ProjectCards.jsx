import { Chip } from './Chip';

// Only shown when a project closes a real evidence gap (skills that cannot be proven in an existing repo).
export default function ProjectCards({ projects }) {
  if (!projects?.length) return null;
  return (
    <div className="bg-white border rounded-lg p-4 mb-4">
      <div className="text-xs font-semibold tracking-wide text-gray-500 mb-2">RECOMMENDED PROJECTS</div>
      <div className="grid md:grid-cols-2 gap-3">
        {projects.map((p) => (
          <div key={p.blueprint_id} className="border rounded p-3">
            <div className="font-semibold">{p.name}</div>
            <p className="text-sm text-gray-600 mt-1">{p.description || p.purpose}</p>
            <div className="mt-2 text-xs text-gray-500">PROVES</div>
            <div className="flex flex-wrap gap-1">
              {p.skills_covered.map((s) => <Chip key={s} spec={{ cls: 'bg-purple-100 text-purple-800' }}>{s}</Chip>)}
            </div>
            {p.also_practises?.length > 0 && (
              <>
                <div className="mt-2 text-xs text-gray-500">ALSO PRACTISES</div>
                <div className="flex flex-wrap gap-1">{p.also_practises.map((s) => <Chip key={s}>{s}</Chip>)}</div>
              </>
            )}
            <div className="mt-2 text-xs text-gray-500">EVIDENCE TO PRODUCE</div>
            <ul className="list-disc ml-4 text-sm">{p.evidence_artifacts.map((a) => <li key={a}>{a}</li>)}</ul>
            <p className="mt-2 text-xs text-gray-400">Tracked as a Build action in your plan.</p>
          </div>
        ))}
      </div>
    </div>
  );
}
