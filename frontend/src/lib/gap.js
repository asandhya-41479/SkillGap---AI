// Helpers that turn Skill Gap results (from the backend) into display data.
// Nothing here changes a score: the numbers all come from the API; this only groups and colours them.

// Same weights the alignment score uses on the backend (required x2, preferred x1, optional x0.5).
export const WEIGHT = { required: 2, preferred: 1, optional: 0.5 };

// One display "status" per requirement: strong, or the gap's priority.
export function statusOf(result) {
  if (result.classification === 'strong') return 'strong';
  if (result.priority === 'high' || result.priority === 'medium' || result.priority === 'low') return result.priority;
  return 'low';
}

export const STATUS = {
  strong: { label: 'Strong', fill: '#2563EB', soft: 'bg-blue-50 text-blue-800 ring-blue-200', text: 'text-strong' },
  high: { label: 'High priority', fill: '#EA580C', soft: 'bg-orange-50 text-orange-800 ring-orange-200', text: 'text-high' },
  medium: { label: 'Medium priority', fill: '#D97706', soft: 'bg-amber-50 text-amber-800 ring-amber-200', text: 'text-medium' },
  low: { label: 'Low priority', fill: '#94A3B8', soft: 'bg-slate-100 text-slate-700 ring-slate-200', text: 'text-slate-600' },
};

export const CLASS_LABEL = { strong: 'Strong match', partial: 'Partial match', transferable: 'Transferable', gap: 'Missing' };
export const IMPORTANCE_LABEL = { required: 'Required', preferred: 'Preferred', optional: 'Optional' };

export function nameOf(result) {
  return result.job_requirement?.skill_name || `Requirement #${result.job_requirement_id}`;
}

export function importanceOf(result) {
  return result.job_requirement?.importance || 'optional';
}

// Two-letter "element" symbol for the periodic table (Python -> Py, LangGraph -> Lg, CI/CD -> Ci).
export function symbolOf(name) {
  const letters = (name || '?').replace(/[^A-Za-z0-9]/g, '');
  if (letters.length <= 2) return letters.charAt(0).toUpperCase() + letters.slice(1).toLowerCase();
  const caps = name.match(/[A-Z]/g) || [];
  if (caps.length >= 2 && /[a-z]/.test(name)) return caps[0] + caps[1].toLowerCase();
  return letters.charAt(0).toUpperCase() + letters.charAt(1).toLowerCase();
}

// Skill areas used by the radar chart (the backend's 10 categories grouped into 6 areas).
export const AREAS = [
  { key: 'core', label: 'Languages & APIs', cats: ['programming_language', 'api'] },
  { key: 'frameworks', label: 'Frameworks', cats: ['framework', 'library'] },
  { key: 'ai', label: 'AI / ML', cats: ['ai_ml'] },
  { key: 'data', label: 'Data', cats: ['database'] },
  { key: 'ops', label: 'Cloud & DevOps', cats: ['cloud', 'devops'] },
  { key: 'tools', label: 'Tools & Concepts', cats: ['tool', 'concept'] },
];

// Coverage per area: strong = 1, partial = 0.5, anything else = 0.
export function areaCoverage(results) {
  return AREAS.map((a) => {
    const items = results.filter((r) => a.cats.includes(r.job_requirement?.category));
    const got = items.reduce((s, r) => s + (r.classification === 'strong' ? 1 : r.classification === 'partial' ? 0.5 : 0), 0);
    return { ...a, total: items.length, strong: items.filter((r) => r.classification === 'strong').length, pct: items.length ? got / items.length : 0 };
  }).filter((a) => a.total > 0);
}

export function countBy(results) {
  const c = { strong: 0, high: 0, medium: 0, low: 0 };
  results.forEach((r) => { c[statusOf(r)] += 1; });
  return c;
}

// Weighted points per requirement that are still missing (used by "points still on the table").
export function missingPoints(result) {
  const w = WEIGHT[importanceOf(result)] ?? 0.5;
  if (result.classification === 'strong') return 0;
  return w;
}

const ORDER = { high: 0, medium: 1, low: 2, strong: 3 };
export function sortByPriority(results) {
  return [...results].sort((a, b) =>
    ORDER[statusOf(a)] - ORDER[statusOf(b)] || (WEIGHT[importanceOf(b)] ?? 0) - (WEIGHT[importanceOf(a)] ?? 0));
}

// The newest analysis of a job (the list endpoint returns summaries for all of the user's analyses).
export function latestAnalysisFor(analyses, jobId) {
  return analyses
    .filter((a) => String(a.job_description_id) === String(jobId) && a.status !== 'failed')
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0] || null;
}

export function fmtPct(v) {
  if (v === null || v === undefined) return '—';
  return `${Math.round(Number(v) * 10) / 10}%`;
}
