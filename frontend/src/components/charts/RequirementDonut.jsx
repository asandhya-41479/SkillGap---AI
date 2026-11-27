import { STATUS } from '../../lib/gap';

// Ring split into one segment per requirement, coloured by status, with the alignment % in the middle.
export default function RequirementDonut({ counts, centre, caption, size = 200 }) {
  const order = ['strong', 'high', 'medium', 'low'];
  const total = order.reduce((s, k) => s + (counts[k] || 0), 0);
  const R = 72, C = 2 * Math.PI * R, GAP = total > 1 ? 2.5 : 0;
  const seg = total ? C / total : 0;
  let i = 0;
  const arcs = [];
  order.forEach((k) => {
    for (let n = 0; n < (counts[k] || 0); n += 1) {
      arcs.push(
        <circle key={`${k}${n}`} cx="90" cy="90" r={R} fill="none" stroke={STATUS[k].fill} strokeWidth="22"
          strokeDasharray={`${Math.max(seg - GAP, 0.5)} ${C}`} strokeDashoffset={-i * seg} />,
      );
      i += 1;
    }
  });
  const aria = `${total} requirements: ${order.map((k) => `${counts[k] || 0} ${STATUS[k].label.toLowerCase()}`).join(', ')}. ${caption || ''} ${centre || ''}`;
  return (
    <svg viewBox="0 0 180 180" width={size} height={size} role="img" aria-label={aria}>
      <circle cx="90" cy="90" r={R} fill="none" stroke="#EEF2F7" strokeWidth="22" />
      <g transform="rotate(-90 90 90)">{arcs}</g>
      <text x="90" y="94" textAnchor="middle" fontFamily="Space Grotesk, Inter, sans-serif" fontSize="34" fontWeight="700" fill="#0F172A">{centre}</text>
      {caption && <text x="90" y="114" textAnchor="middle" fontFamily="Inter, sans-serif" fontSize="11" fill="#475569">{caption}</text>}
    </svg>
  );
}
