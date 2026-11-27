import { Chip } from './Chip';

// Only shown when a project closes a real evidence gap (skills that cannot be proven in an existing repo).
// Each card opens to show the full project details.
export default function ProjectCards({ projects }) {
  if (!projects?.length) return null;
  return (
    <section className="card flex flex-col gap-3">
      <div>
        <h2 className="m-0 font-display text-lg font-bold">Recommended projects</h2>
        <p className="m-0 mt-1 text-sm text-muted">Each project proves several missing skills at once. Open a card for the details.</p>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        {projects.map((p) => (
          <details key={p.blueprint_id} className="group rounded-2xl border-[1.5px] border-line bg-white p-4 open:border-brand">
            <summary className="flex cursor-pointer list-none flex-col gap-2">
              <span className="flex items-start justify-between gap-3">
                <span className="font-display text-base font-bold text-ink">{p.name}</span>
                <span className="flex-none rounded-full bg-green-100 px-2.5 py-1 text-xs font-bold text-green-800">
                  Proves {p.skills_covered.length} skill{p.skills_covered.length === 1 ? '' : 's'}
                </span>
              </span>
              <span className="text-sm text-slate-700">{p.purpose}</span>
              <span className="flex flex-wrap gap-1">
                {p.skills_covered.map((s) => <Chip key={s} spec={{ cls: 'bg-brand-soft text-brand-dark' }}>{s}</Chip>)}
              </span>
              <span className="text-sm font-semibold text-brand group-open:hidden">Show project details ▾</span>
            </summary>
            <div className="mt-3 flex flex-col gap-2 border-t border-line pt-3 text-sm text-slate-700">
              {p.description && <p className="m-0 leading-relaxed">{p.description}</p>}
              {p.also_practises?.length > 0 && (
                <div>
                  <p className="eyebrow m-0 mb-1">Also practises</p>
                  <div className="flex flex-wrap gap-1">{p.also_practises.map((s) => <Chip key={s}>{s}</Chip>)}</div>
                </div>
              )}
              <div>
                <p className="eyebrow m-0 mb-1">Evidence to produce</p>
                <ul className="m-0 list-disc pl-5">{p.evidence_artifacts.map((a) => <li key={a}>{a}</li>)}</ul>
              </div>
              <p className="m-0 text-xs text-muted">Tracked as a Build action in your plan.</p>
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}
