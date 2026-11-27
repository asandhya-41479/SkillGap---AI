// "You vs the job" radar: the job needs 100% of every area (dashed orange); your coverage is the blue shape.
// With fewer than 3 areas a radar is meaningless, so it falls back to bars.
export default function AreaRadar({ areas }) {
  if (areas.length < 3) {
    return (
      <ul className="m-0 flex list-none flex-col gap-3 p-0">
        {areas.map((a) => (
          <li key={a.key}>
            <div className="mb-1.5 flex justify-between text-sm"><strong>{a.label}</strong><span className="text-muted">{a.strong}/{a.total} strong</span></div>
            <div className="h-3 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-brand" style={{ width: `${a.pct * 100}%` }} /></div>
          </li>
        ))}
      </ul>
    );
  }
  const cx = 160, cy = 150, R = 100, n = areas.length;
  const pt = (i, r) => {
    const ang = (-90 + (360 / n) * i) * (Math.PI / 180);
    return [cx + r * Math.cos(ang), cy + r * Math.sin(ang)];
  };
  const poly = (fn) => areas.map((a, i) => pt(i, fn(a)).map((v) => v.toFixed(1)).join(',')).join(' ');
  const aria = 'Coverage by skill area: ' + areas.map((a) => `${a.label} ${a.strong} of ${a.total} strong`).join('; ');
  return (
    <svg viewBox="-80 0 480 300" width="100%" style={{ maxWidth: 460 }} role="img" aria-label={aria}>
      {[1, 0.5].map((f) => <polygon key={f} points={poly(() => R * f)} fill={f === 1 ? '#F8FAFF' : 'none'} stroke="#E2E8F0" strokeWidth="1.5" />)}
      {areas.map((a, i) => { const [x, y] = pt(i, R); return <line key={a.key} x1={cx} y1={cy} x2={x} y2={y} stroke="#E2E8F0" strokeWidth="1.5" />; })}
      <polygon points={poly(() => R)} fill="none" stroke="#F97316" strokeWidth="2.5" strokeDasharray="6 5" />
      <polygon points={poly((a) => Math.max(R * a.pct, 4))} fill="#2563EB" fillOpacity="0.22" stroke="#2563EB" strokeWidth="3" strokeLinejoin="round" />
      {areas.map((a, i) => { const [x, y] = pt(i, Math.max(R * a.pct, 4)); return <circle key={a.key} cx={x} cy={y} r="5" fill="#2563EB" />; })}
      {areas.map((a, i) => {
        const [x, y] = pt(i, R + 22);
        const anchor = Math.abs(x - cx) < 10 ? 'middle' : x > cx ? 'start' : 'end';
        return (
          <text key={a.key} x={x} y={y} textAnchor={anchor} fontFamily="Inter, sans-serif" fontSize="11.5" fontWeight="600" fill="#0F172A">
            <tspan x={x} dy="-2">{a.label}</tspan>
            <tspan x={x} dy="14" fill={a.pct >= 0.99 ? '#15803D' : a.pct < 0.34 ? '#C2410C' : '#475569'}>{a.strong}/{a.total}</tspan>
          </text>
        );
      })}
    </svg>
  );
}
