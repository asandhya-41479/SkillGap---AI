import { CATEGORY, PRIORITY, SKILL_STATE } from './labels';
import { Chip } from './Chip';
import { IMPORTANCE_TEXT } from '../readiness/labels';

// Ranked by the backend priority formula (requirement, severity, importance, dependency, progress).
export default function SkillPriorities({ rows }) {
  if (!rows?.length) return null;
  return (
    <div className="bg-white border rounded-lg p-4 mb-4">
      <div className="text-xs font-semibold tracking-wide text-gray-500 mb-2">SKILL PRIORITIES</div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-gray-500 border-b">
              <th className="py-1 pr-2">Skill</th><th className="pr-2">Role needs it</th><th className="pr-2">Your state</th>
              <th className="pr-2">Action</th><th>Priority</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.skill_name} className="border-b last:border-0 align-top" title={r.reason}>
                <td className="py-1.5 pr-2 font-medium">{r.skill_name}</td>
                <td className="pr-2">{IMPORTANCE_TEXT[r.importance] || r.importance}</td>
                <td className="pr-2">{SKILL_STATE[r.state] || r.state}</td>
                <td className="pr-2"><Chip spec={CATEGORY[r.category]} /></td>
                <td><Chip spec={PRIORITY[r.priority]} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-gray-400 mt-2">Hover a row to see why it has this priority.</p>
    </div>
  );
}
