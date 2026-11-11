// Display text only. The strengths themselves are set by the backend (readiness_config.py).

export const evidenceLabel = (s) => {
  if (s >= 1) return { text: 'Verified GitHub work', cls: 'bg-green-100 text-green-800' };
  if (s >= 0.6) return { text: 'Supporting evidence', cls: 'bg-blue-100 text-blue-800' };
  if (s >= 0.4) return { text: 'Project link (not checked)', cls: 'bg-sky-100 text-sky-800' };
  if (s > 0) return { text: 'Learning only', cls: 'bg-amber-100 text-amber-800' };
  return { text: 'No evidence', cls: 'bg-gray-100 text-gray-600' };
};

export const CLASSIFICATION_TEXT = { strong: 'Strong match', partial: 'Partial', transferable: 'Transferable', gap: 'Gap' };

export const IMPORTANCE_TEXT = { required: 'Required', preferred: 'Preferred', optional: 'Optional' };

export const STATUS_TEXT = {
  verified: { text: 'Verified', cls: 'bg-green-100 text-green-800' },
  linked: { text: 'Linked, not verified', cls: 'bg-sky-100 text-sky-800' },
  unverified: { text: 'Checked: no signal found', cls: 'bg-amber-100 text-amber-800' },
  unavailable: { text: 'GitHub unreachable, retry', cls: 'bg-gray-100 text-gray-600' },
};

export const errorText = (err, fallback) =>
  typeof err?.response?.data?.detail === 'string' ? err.response.data.detail : fallback;
