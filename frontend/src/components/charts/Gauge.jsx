// Half-circle gauge for a 0-100 score. `previous` (optional) shows the earlier score as a lighter arc.
export default function Gauge({ value, previous = null, label, size = 300 }) {
  const R = 120, C = Math.PI * R;
  const v = Math.max(0, Math.min(100, Number(value) || 0));
  const p = previous === null || previous === undefined ? null : Math.max(0, Math.min(100, Number(previous)));
  const has = value !== null && value !== undefined;
  const aria = has
    ? `Score ${Math.round(v)} out of 100${p !== null ? `, previously ${Math.round(p)}` : ''}`
    : 'Not enough data for a score yet';
  return (
    <svg viewBox="0 0 300 178" width="100%" style={{ maxWidth: size }} role="img" aria-label={aria}>
      <path d="M30 160 A120 120 0 0 1 270 160" fill="none" stroke="#EEF2F7" strokeWidth="26" strokeLinecap="round" />
      {p !== null && (
        <path d="M30 160 A120 120 0 0 1 270 160" fill="none" stroke="#C7D2FE" strokeWidth="26" strokeLinecap="round"
          strokeDasharray={`${(C * p) / 100} ${C}`} />
      )}
      {has && (
        <path d="M30 160 A120 120 0 0 1 270 160" fill="none" stroke="#2563EB" strokeWidth="26" strokeLinecap="round"
          strokeDasharray={`${(C * v) / 100} ${C}`} />
      )}
      <text x="150" y="136" textAnchor="middle" fontFamily="Space Grotesk, Inter, sans-serif" fontSize="66" fontWeight="700" fill="#0F172A">
        {has ? Math.round(v) : '—'}
      </text>
      <text x="150" y="162" textAnchor="middle" fontFamily="Inter, sans-serif" fontSize="13" fill="#475569">
        {label || 'out of 100'}
      </text>
    </svg>
  );
}
