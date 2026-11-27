import { STATUS, statusOf, nameOf } from '../../lib/gap';

// "Your skill map": the score sits in the centre, strong skills orbit close, gaps orbit further out
// (bigger dot = higher priority). Built only from the analysis results the API returns.
const SIZE = { strong: 8, high: 12, medium: 9, low: 6.5 };

function shorten(s) {
  return s.length > 16 ? `${s.slice(0, 15)}…` : s;
}

export default function Constellation({ results, centreValue, centreLabel }) {
  const cx = 330, cy = 250, R1 = 112, R2 = 212;
  const strong = results.filter((r) => statusOf(r) === 'strong');
  const gaps = results.filter((r) => statusOf(r) !== 'strong');

  const place = (list, R, offset) =>
    list.map((r, i) => {
      const ang = ((-90 + offset + (360 / Math.max(list.length, 1)) * i) * Math.PI) / 180;
      return { r, x: cx + R * Math.cos(ang), y: cy + R * Math.sin(ang), right: Math.cos(ang) >= 0 };
    });
  const inner = place(strong, R1, 360 / Math.max(strong.length, 1) / 2);
  const outer = place(gaps, R2, 0);

  const aria = `Skill map. Centre: ${centreLabel} ${centreValue}. ${strong.length} strong skills on the inner orbit: ${strong.map(nameOf).join(', ') || 'none'}. ${gaps.length} gaps on the outer orbit: ${gaps.map(nameOf).join(', ') || 'none'}.`;

  return (
    <svg viewBox="0 0 660 500" width="100%" role="img" aria-label={aria}>
      <defs>
        <filter id="cn-glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="4" result="b" />
          <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <radialGradient id="cn-bg" cx="50%" cy="50%" r="60%">
          <stop offset="0" stopColor="#13244D" />
          <stop offset="1" stopColor="#071026" />
        </radialGradient>
      </defs>
      <rect width="660" height="500" rx="18" fill="url(#cn-bg)" />
      <g fill="#FFFFFF" opacity="0.45">
        <circle cx="40" cy="40" r="1.2" /><circle cx="610" cy="60" r="1" /><circle cx="630" cy="430" r="1.4" />
        <circle cx="30" cy="460" r="1" /><circle cx="520" cy="480" r="1.2" /><circle cx="140" cy="30" r="1" />
      </g>
      <circle cx={cx} cy={cy} r={R1} fill="none" stroke="#1E3A5F" strokeWidth="1.5" strokeDasharray="3 6" />
      <circle cx={cx} cy={cy} r={R2} fill="none" stroke="#3B2A1E" strokeWidth="1.5" strokeDasharray="3 6" />
      {inner.map(({ r, x, y }) => <line key={`l${r.id}`} x1={cx} y1={cy} x2={x} y2={y} stroke="#22D3EE" strokeOpacity="0.22" strokeWidth="1.5" />)}

      <circle cx={cx} cy={cy} r="74" fill="#0E1A33" />
      <circle cx={cx} cy={cy} r="62" fill="none" stroke="#1A2442" strokeWidth="10" />
      {typeof centreValue === 'number' && (
        <circle cx={cx} cy={cy} r="62" fill="none" stroke="#22D3EE" strokeWidth="10" strokeLinecap="round" filter="url(#cn-glow)"
          strokeDasharray={`${(2 * Math.PI * 62 * Math.min(centreValue, 100)) / 100} ${2 * Math.PI * 62}`} transform={`rotate(-90 ${cx} ${cy})`} />
      )}
      <text x={cx} y={cy + 12} textAnchor="middle" fontFamily="Space Grotesk, Inter, sans-serif" fontSize="42" fontWeight="700" fill="#FFFFFF">
        {typeof centreValue === 'number' ? Math.round(centreValue) : '—'}
      </text>
      <text x={cx} y={cy + 32} textAnchor="middle" fontFamily="Inter, sans-serif" fontSize="10.5" fontWeight="600" fill="#94A3C4" letterSpacing="1">
        {(centreLabel || '').toUpperCase()}
      </text>

      <g filter="url(#cn-glow)">
        {inner.map(({ r, x, y }) => <circle key={r.id} cx={x} cy={y} r={SIZE.strong} fill="#22D3EE" />)}
        {outer.map(({ r, x, y }) => <circle key={r.id} cx={x} cy={y} r={SIZE[statusOf(r)]} fill={STATUS[statusOf(r)].fill} />)}
      </g>
      {[...inner, ...outer].map(({ r, x, y, right }) => {
        const st = statusOf(r);
        const dx = (SIZE[st] + 6) * (right ? 1 : -1);
        return (
          <text key={`t${r.id}`} x={x + dx} y={y + 4} textAnchor={right ? 'start' : 'end'} fontFamily="Inter, sans-serif"
            fontSize={st === 'high' ? 13 : 12} fontWeight={st === 'high' ? 700 : 600}
            fill={st === 'strong' ? '#E6ECF8' : st === 'high' ? '#FDBA74' : st === 'medium' ? '#FCD34D' : '#A9B6D3'}>
            {shorten(nameOf(r))}
          </text>
        );
      })}
    </svg>
  );
}
