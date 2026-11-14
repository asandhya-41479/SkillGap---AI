// Display text and colours only. Every value they describe comes from the backend.

export const CAREER_STATUS = {
  BUILDING_FOUNDATION: { text: 'Building foundation', cls: 'bg-gray-100 text-gray-800 border-gray-300' },
  DEVELOPING: { text: 'Developing', cls: 'bg-amber-50 text-amber-800 border-amber-300' },
  NEAR_READY: { text: 'Near ready', cls: 'bg-blue-50 text-blue-800 border-blue-300' },
  READY_TO_APPLY: { text: 'Ready to apply', cls: 'bg-green-50 text-green-800 border-green-300' },
};

export const CATEGORY = {
  LEARN: { text: 'Learn', cls: 'bg-sky-100 text-sky-800' },
  PRACTICE: { text: 'Practice', cls: 'bg-indigo-100 text-indigo-800' },
  BUILD: { text: 'Build', cls: 'bg-purple-100 text-purple-800' },
  PROVE: { text: 'Prove', cls: 'bg-fuchsia-100 text-fuchsia-800' },
  PREPARE: { text: 'Prepare', cls: 'bg-teal-100 text-teal-800' },
  APPLY: { text: 'Apply', cls: 'bg-green-100 text-green-800' },
};

export const PRIORITY = {
  HIGH: { text: 'High', cls: 'bg-red-100 text-red-800' },
  MEDIUM: { text: 'Medium', cls: 'bg-amber-100 text-amber-800' },
  LOW: { text: 'Low', cls: 'bg-gray-100 text-gray-700' },
};

export const ACTION_STATUS = [
  ['NOT_STARTED', 'Not started'],
  ['IN_PROGRESS', 'In progress'],
  ['COMPLETED', 'Completed'],
  ['SKIPPED', 'Skipped'],
];

export const SKILL_STATE = {
  NO_KNOWLEDGE: 'Gap',
  TRANSFERABLE: 'Related foundation',
  PARTIAL: 'Partial',
  KNOWN_NO_EVIDENCE: 'Known, not proven',
  PROVEN: 'Proven',
};

export const PREP_KIND = {
  GAP: 'Skill gaps',
  PROJECT: 'Your SkillGap AI project',
  ROLE: 'Role fundamentals',
};

export const criterionValue = (c) => {
  if (c.value === null || c.value === undefined) {
    return c.key === 'P' ? 'no active roadmap (not counted)' : 'not available yet';
  }
  if (c.key === 'C') return String(c.value);
  if (c.key === 'S') return `${Math.round(c.value)} / 100`;
  return `${Math.round(c.value)}%`;
};

// C is a count, S a score out of 100, the rest are percentages
export const criterionTarget = (c) => `${c.comparator} ${c.key === 'C' || c.key === 'S' ? c.threshold : `${c.threshold}%`}`;
