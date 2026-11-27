// Brand mark: a small bridge with the "next skill" dot. `dark` = for use on white backgrounds.
export default function Logo({ dark = false, tagline = false }) {
  return (
    <div className="flex items-center gap-3">
      <svg width="36" height="36" viewBox="0 0 40 40" aria-hidden="true">
        <rect width="40" height="40" rx="12" fill="#2563EB" />
        <path d="M8 26h7l3-6h6l3 6h5" stroke="#FFFFFF" strokeWidth="2.6" fill="none" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="21" cy="12" r="3" fill="#F97316" />
      </svg>
      <div>
        <p className={`m-0 font-display text-lg font-bold leading-tight ${dark ? 'text-ink' : 'text-white'}`}>SkillGap AI</p>
        {tagline && <p className="m-0 text-[13px] text-blue-300">Your skills. Your future.</p>}
      </div>
    </div>
  );
}
