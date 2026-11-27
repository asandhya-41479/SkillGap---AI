// Hand-drawn SVG illustration for the Login and Register pages ("Build the bridge" story).
// Planks = skills; solid blue = proven, dashed = still to build. The numbers on the cards are
// an illustrative example of what the app shows after an analysis.
export function LoginBridge() {
  return (
<svg viewBox="0 0 760 470" className="-mx-6 block h-auto w-[calc(100%+3rem)] lg:-mx-12 lg:w-[calc(100%+6rem)]" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Illustration: a professional stands at the edge of a bridge built from skill planks — Python, FastAPI, Git and SQL — while the next plank, LLM, glows into place. RAG and LangChain are still missing. On the far side is a glowing city labelled Dream Role: Agentic AI Engineer.">
<defs>
<filter id="blur40" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="42" /></filter>
<filter id="glowO" x="-30%" y="-80%" width="160%" height="260%"><feGaussianBlur stdDeviation="4" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
<linearGradient id="city" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#3B82F6" /><stop offset="1" stopColor="#1E3A8A" /></linearGradient>
<linearGradient id="rock" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#1B3168" /><stop offset="1" stopColor="#0B1838" /></linearGradient>
<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#071026" stopOpacity="0" /><stop offset="1" stopColor="#071026" stopOpacity="1" /></linearGradient>
</defs>
<circle cx="665" cy="215" r="135" fill="#2563EB" opacity="0.5" filter="url(#blur40)" />
<g fill="#FFFFFF"><circle cx="60" cy="40" r="1.4" opacity=".7" /><circle cx="190" cy="70" r="1" opacity=".5" /><circle cx="320" cy="30" r="1.6" opacity=".8" /><circle cx="430" cy="80" r="1.1" opacity=".5" /><circle cx="520" cy="24" r="1.3" opacity=".7" /><circle cx="745" cy="40" r="1.5" opacity=".7" /><circle cx="110" cy="170" r="1" opacity=".5" /><circle cx="480" cy="150" r="1.2" opacity=".6" /><circle cx="270" cy="140" r="1" opacity=".4" /></g>
<g stroke="#1E3366" strokeDasharray="2 10" strokeWidth="1.5"><line x1="160" y1="392" x2="600" y2="392" /><line x1="190" y1="420" x2="570" y2="420" /></g>
<path d="M0 332 L152 328 L146 362 L122 470 L0 470 Z" fill="url(#rock)" />
<path d="M0 332 L152 328" stroke="#3B5BA9" strokeWidth="2" />
<path d="M602 328 L760 324 L760 470 L630 470 L610 372 Z" fill="url(#rock)" />
<path d="M602 328 L760 324" stroke="#3B5BA9" strokeWidth="2" />
<g>
<rect x="622" y="236" width="34" height="90" rx="3" fill="url(#city)" />
<rect x="660" y="174" width="46" height="152" rx="3" fill="url(#city)" />
<rect x="710" y="220" width="30" height="106" rx="3" fill="url(#city)" />
<rect x="742" y="262" width="18" height="64" rx="3" fill="url(#city)" />
<g fill="#BAE6FD"><rect x="629" y="248" width="6" height="6" rx="1" /><rect x="643" y="248" width="6" height="6" rx="1" opacity=".5" /><rect x="629" y="264" width="6" height="6" rx="1" opacity=".6" /><rect x="643" y="282" width="6" height="6" rx="1" /><rect x="668" y="188" width="7" height="7" rx="1" /><rect x="684" y="188" width="7" height="7" rx="1" opacity=".5" /><rect x="668" y="206" width="7" height="7" rx="1" opacity=".7" /><rect x="684" y="224" width="7" height="7" rx="1" /><rect x="668" y="242" width="7" height="7" rx="1" /><rect x="684" y="260" width="7" height="7" rx="1" opacity=".6" /><rect x="668" y="278" width="7" height="7" rx="1" opacity=".5" /><rect x="717" y="234" width="6" height="6" rx="1" /><rect x="728" y="250" width="6" height="6" rx="1" opacity=".6" /><rect x="717" y="268" width="6" height="6" rx="1" opacity=".8" /></g>
<line x1="683" y1="174" x2="683" y2="134" stroke="#E2E8F0" strokeWidth="2" />
<path d="M683 134 L711 142 L683 150 Z" fill="#F97316" />
</g>
<g>
<rect x="548" y="58" width="196" height="54" rx="14" fill="#FFFFFF" />
<text x="566" y="80" fontFamily="Inter, Arial, sans-serif" fontSize="10.5" fontWeight="700" fill="#2563EB" letterSpacing="1">DREAM ROLE</text>
<text x="566" y="100" fontFamily="Space Grotesk, Inter, Arial, sans-serif" fontSize="16" fontWeight="700" fill="#0F172A">Agentic AI Engineer</text>
<path d="M670 112 L680 124 L690 112 Z" fill="#FFFFFF" />
</g>
<rect x="140" y="186" width="12" height="144" rx="3" fill="#2B4A80" />
<rect x="602" y="186" width="12" height="144" rx="3" fill="#2B4A80" />
<path d="M146 190 Q 379 320 608 190" fill="none" stroke="#60A5FA" strokeWidth="3" />
<g stroke="#60A5FA" strokeWidth="1.5" opacity="0.75"><line x1="182" y1="208" x2="182" y2="322" /><line x1="247" y1="234" x2="247" y2="322" /><line x1="312" y1="249" x2="312" y2="322" /></g>
<g stroke="#FB923C" strokeWidth="1.5" strokeDasharray="3 4" opacity="0.85"><line x1="442" y1="250" x2="442" y2="322" /><line x1="507" y1="235" x2="507" y2="322" /><line x1="572" y1="210" x2="572" y2="322" /></g>
<g fontFamily="Inter, Arial, sans-serif" fontSize="11.5" fontWeight="700" textAnchor="middle"><rect x="150" y="322" width="60" height="26" rx="5" fill="#2563EB" /><rect x="150" y="322" width="60" height="6" rx="3" fill="#60A5FA" /><text x="180" y="341" fill="#FFFFFF">Python</text><rect x="215" y="322" width="60" height="26" rx="5" fill="#2563EB" /><rect x="215" y="322" width="60" height="6" rx="3" fill="#60A5FA" /><text x="245" y="341" fill="#FFFFFF">FastAPI</text><rect x="280" y="322" width="60" height="26" rx="5" fill="#2563EB" /><rect x="280" y="322" width="60" height="6" rx="3" fill="#60A5FA" /><text x="310" y="341" fill="#FFFFFF">Git</text><rect x="345" y="322" width="60" height="26" rx="5" fill="#2563EB" /><rect x="345" y="322" width="60" height="6" rx="3" fill="#60A5FA" /><text x="375" y="341" fill="#FFFFFF">SQL</text><rect x="410" y="322" width="60" height="26" rx="5" fill="none" stroke="#FB923C" strokeWidth="1.6" strokeDasharray="5 4" opacity="0.8" /><path d="M440 304 v10" stroke="#FDBA74" strokeWidth="1.6" strokeDasharray="2 3" /><polygon points="414,298 466,298 472,330 408,330" fill="#F97316" opacity="0.10" /><g filter="url(#glowO)"><rect x="410" y="276" width="60" height="24" rx="5" fill="#F97316" /><rect x="410" y="276" width="60" height="6" rx="3" fill="#FDBA74" /></g><text x="440" y="294" fill="#FFFFFF">LLM</text><rect x="475" y="322" width="60" height="26" rx="5" fill="#F97316" fillOpacity="0.10" stroke="#FB923C" strokeWidth="1.6" strokeDasharray="5 4" /><text x="505" y="339.5" fill="#FDBA74" fontSize="10.5">RAG</text><rect x="540" y="322" width="60" height="26" rx="5" fill="#F97316" fillOpacity="0.10" stroke="#FB923C" strokeWidth="1.6" strokeDasharray="5 4" /><text x="570" y="339.5" fill="#FDBA74" fontSize="10.5">LangChain</text></g>
<g aria-hidden="true" transform="translate(381 322) scale(1.22) translate(-381 -322)">
<ellipse cx="381" cy="322" rx="24" ry="3.2" fill="#000000" opacity="0.45" />
<path d="M367 279 L381 279 L379 319 L370 319 Z" fill="#1E3A8A" />
<path d="M382 279 L396 279 L394 319 L385 319 Z" fill="#1B3478" />
<rect x="366" y="316" width="14" height="6" rx="3" fill="#0B1220" />
<rect x="383" y="316" width="14" height="6" rx="3" fill="#0B1220" />
<path d="M366 244 L360 281" stroke="#CBD7EE" strokeWidth="8" strokeLinecap="round" />
<path d="M397 244 L403 281" stroke="#B9C8E6" strokeWidth="8" strokeLinecap="round" />
<circle cx="360" cy="284" r="3.8" fill="#D9A27E" />
<circle cx="403" cy="284" r="3.8" fill="#C98F6B" />
<path d="M365 241 C 371 236, 391 236, 397 241 L 400 282 L 362 282 Z" fill="#DCE6F7" />
<path d="M381 237 C 388 237, 393 238, 397 241 L 400 282 L 381 282 Z" fill="#C3D2EE" />
<path d="M381 240 L381 282" stroke="#AFC1E3" strokeWidth="1.2" />
<path d="M367 243 L 395 276" stroke="#334155" strokeWidth="2.4" />
<rect x="391" y="268" width="13" height="14" rx="2.5" fill="#334155" />
<rect x="377.5" y="230" width="7" height="8" rx="2" fill="#C98F6B" />
<circle cx="371.6" cy="223" r="2.4" fill="#C98F6B" /><circle cx="390.4" cy="223" r="2.4" fill="#C98F6B" />
<ellipse cx="381" cy="221" rx="9" ry="10.5" fill="#111827" />
<path d="M373 216 C 377 211, 386 211, 389 216" stroke="#334155" strokeWidth="1.5" fill="none" />
<path d="M398 242 L401 281" stroke="#93C5FD" strokeWidth="1.2" opacity="0.8" />
</g>
<g fontFamily="Inter, Arial, sans-serif">
<rect x="40" y="118" width="176" height="48" rx="12" fill="#0E1B3D" stroke="#2B4A80" />
<circle cx="62" cy="142" r="10" fill="#14532D" /><path d="M57 145 l3-4 l3 3 l4-6" stroke="#4ADE80" strokeWidth="1.8" fill="none" strokeLinecap="round" />
<text x="80" y="137" fontSize="10" fill="#93C5FD" fontWeight="700" letterSpacing=".5">READINESS</text>
<text x="80" y="155" fontSize="14" fill="#FFFFFF" fontWeight="700">29 → 44  (+15)</text>
<rect x="250" y="86" width="200" height="48" rx="12" fill="#0E1B3D" stroke="#9A3412" />
<circle cx="272" cy="110" r="10" fill="#431407" /><text x="272" y="114.5" textAnchor="middle" fontSize="12" fontWeight="800" fill="#FB923C">!</text>
<text x="290" y="105" fontSize="10" fill="#FDBA74" fontWeight="700" letterSpacing=".5">NEXT STEP</text>
<text x="290" y="123" fontSize="14" fill="#FFFFFF" fontWeight="700">Add evidence for LLM</text>
<rect x="430" y="366" width="176" height="48" rx="12" fill="#0E1B3D" stroke="#2B4A80" />
<circle cx="452" cy="390" r="10" fill="#14532D" /><path d="M447 390 l3 3 l6-7" stroke="#4ADE80" strokeWidth="1.8" fill="none" strokeLinecap="round" />
<text x="470" y="385" fontSize="10" fill="#93C5FD" fontWeight="700" letterSpacing=".5">VERIFIED ON GITHUB</text>
<text x="470" y="403" fontSize="14" fill="#FFFFFF" fontWeight="700">FastAPI</text>
</g>
<rect x="0" y="400" width="760" height="70" fill="url(#fade)" />
</svg>
  );
}

export function RegisterBridge() {
  return (
<svg viewBox="0 0 760 470" className="-mx-6 block h-auto w-[calc(100%+3rem)] lg:-mx-12 lg:w-[calc(100%+6rem)]" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Illustration: a professional stands at the start of a bridge where only the first plank, Python, is in place. FastAPI, Git, SQL, LLM, RAG and LangChain are outlined, still to be built. On the far side is a glowing city labelled Dream Role: Agentic AI Engineer.">
<defs>
<filter id="r-blur40" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="42" /></filter>
<filter id="r-glowB" x="-30%" y="-80%" width="160%" height="260%"><feGaussianBlur stdDeviation="5" result="b" /><feFlood floodColor="#3B82F6" /><feComposite in2="b" operator="in" /><feMerge><feMergeNode /><feMergeNode in="SourceGraphic" /></feMerge></filter>
<filter id="r-glowO" x="-30%" y="-80%" width="160%" height="260%"><feGaussianBlur stdDeviation="4" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
<linearGradient id="r-city" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#3B82F6" /><stop offset="1" stopColor="#1E3A8A" /></linearGradient>
<linearGradient id="r-rock" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#1B3168" /><stop offset="1" stopColor="#0B1838" /></linearGradient>
<linearGradient id="r-fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#071026" stopOpacity="0" /><stop offset="1" stopColor="#071026" stopOpacity="1" /></linearGradient>
</defs>
<circle cx="665" cy="215" r="135" fill="#2563EB" opacity="0.5" filter="url(#r-blur40)" />
<g fill="#FFFFFF"><circle cx="60" cy="40" r="1.4" opacity=".7" /><circle cx="190" cy="70" r="1" opacity=".5" /><circle cx="320" cy="30" r="1.6" opacity=".8" /><circle cx="430" cy="80" r="1.1" opacity=".5" /><circle cx="520" cy="24" r="1.3" opacity=".7" /><circle cx="745" cy="40" r="1.5" opacity=".7" /><circle cx="110" cy="170" r="1" opacity=".5" /><circle cx="480" cy="150" r="1.2" opacity=".6" /><circle cx="270" cy="140" r="1" opacity=".4" /></g>
<g stroke="#1E3366" strokeDasharray="2 10" strokeWidth="1.5"><line x1="160" y1="392" x2="600" y2="392" /><line x1="190" y1="420" x2="570" y2="420" /></g>
<path d="M0 332 L152 328 L146 362 L122 470 L0 470 Z" fill="url(#r-rock)" />
<path d="M0 332 L152 328" stroke="#3B5BA9" strokeWidth="2" />
<path d="M602 328 L760 324 L760 470 L630 470 L610 372 Z" fill="url(#r-rock)" />
<path d="M602 328 L760 324" stroke="#3B5BA9" strokeWidth="2" />
<g>
<rect x="622" y="236" width="34" height="90" rx="3" fill="url(#r-city)" />
<rect x="660" y="174" width="46" height="152" rx="3" fill="url(#r-city)" />
<rect x="710" y="220" width="30" height="106" rx="3" fill="url(#r-city)" />
<rect x="742" y="262" width="18" height="64" rx="3" fill="url(#r-city)" />
<g fill="#BAE6FD"><rect x="629" y="248" width="6" height="6" rx="1" /><rect x="643" y="248" width="6" height="6" rx="1" opacity=".5" /><rect x="629" y="264" width="6" height="6" rx="1" opacity=".6" /><rect x="643" y="282" width="6" height="6" rx="1" /><rect x="668" y="188" width="7" height="7" rx="1" /><rect x="684" y="188" width="7" height="7" rx="1" opacity=".5" /><rect x="668" y="206" width="7" height="7" rx="1" opacity=".7" /><rect x="684" y="224" width="7" height="7" rx="1" /><rect x="668" y="242" width="7" height="7" rx="1" /><rect x="684" y="260" width="7" height="7" rx="1" opacity=".6" /><rect x="668" y="278" width="7" height="7" rx="1" opacity=".5" /><rect x="717" y="234" width="6" height="6" rx="1" /><rect x="728" y="250" width="6" height="6" rx="1" opacity=".6" /><rect x="717" y="268" width="6" height="6" rx="1" opacity=".8" /></g>
<line x1="683" y1="174" x2="683" y2="134" stroke="#E2E8F0" strokeWidth="2" />
<path d="M683 134 L711 142 L683 150 Z" fill="#F97316" />
</g>
<g>
<rect x="548" y="58" width="196" height="54" rx="14" fill="#FFFFFF" />
<text x="566" y="80" fontFamily="Inter, Arial, sans-serif" fontSize="10.5" fontWeight="700" fill="#2563EB" letterSpacing="1">DREAM ROLE</text>
<text x="566" y="100" fontFamily="Space Grotesk, Inter, Arial, sans-serif" fontSize="16" fontWeight="700" fill="#0F172A">Agentic AI Engineer</text>
<path d="M670 112 L680 124 L690 112 Z" fill="#FFFFFF" />
</g>
<rect x="140" y="186" width="12" height="144" rx="3" fill="#2B4A80" />
<rect x="602" y="186" width="12" height="144" rx="3" fill="#2B4A80" />
<path d="M146 190 Q 379 320 608 190" fill="none" stroke="#60A5FA" strokeWidth="3" />
<g stroke="#5B7DB8" strokeWidth="1.5" strokeDasharray="3 4" opacity="0.85"><line x1="182" y1="208" x2="182" y2="322" /><line x1="247" y1="234" x2="247" y2="322" /><line x1="312" y1="249" x2="312" y2="322" /></g>
<g stroke="#5B7DB8" strokeWidth="1.5" strokeDasharray="3 4" opacity="0.85"><line x1="442" y1="250" x2="442" y2="322" /><line x1="507" y1="235" x2="507" y2="322" /><line x1="572" y1="210" x2="572" y2="322" /></g>
<g fontFamily="Inter, Arial, sans-serif" fontSize="11.5" fontWeight="700" textAnchor="middle"><g filter="url(#r-glowB)"><rect x="150" y="322" width="60" height="26" rx="5" fill="#2563EB" /><rect x="150" y="322" width="60" height="6" rx="3" fill="#93C5FD" /></g><text x="180" y="341" fill="#FFFFFF">Python</text><rect x="215" y="322" width="60" height="26" rx="5" fill="#93C5FD" fillOpacity="0.05" stroke="#5B7DB8" strokeWidth="1.5" strokeDasharray="5 4" /><text x="245" y="339.5" fill="#9FB4DA" fontSize="10.5">FastAPI</text><rect x="280" y="322" width="60" height="26" rx="5" fill="#93C5FD" fillOpacity="0.05" stroke="#5B7DB8" strokeWidth="1.5" strokeDasharray="5 4" /><text x="310" y="339.5" fill="#9FB4DA" fontSize="10.5">Git</text><rect x="345" y="322" width="60" height="26" rx="5" fill="#93C5FD" fillOpacity="0.05" stroke="#5B7DB8" strokeWidth="1.5" strokeDasharray="5 4" /><text x="375" y="339.5" fill="#9FB4DA" fontSize="10.5">SQL</text><rect x="410" y="322" width="60" height="26" rx="5" fill="#93C5FD" fillOpacity="0.05" stroke="#5B7DB8" strokeWidth="1.5" strokeDasharray="5 4" /><text x="440" y="339.5" fill="#9FB4DA" fontSize="10.5">LLM</text><rect x="475" y="322" width="60" height="26" rx="5" fill="#93C5FD" fillOpacity="0.05" stroke="#5B7DB8" strokeWidth="1.5" strokeDasharray="5 4" /><text x="505" y="339.5" fill="#9FB4DA" fontSize="10.5">RAG</text><rect x="540" y="322" width="60" height="26" rx="5" fill="#93C5FD" fillOpacity="0.05" stroke="#5B7DB8" strokeWidth="1.5" strokeDasharray="5 4" /><text x="570" y="339.5" fill="#9FB4DA" fontSize="10.5">LangChain</text></g>
<g aria-hidden="true" transform="translate(-292 7) translate(381 322) scale(1.22) translate(-381 -322)">
<ellipse cx="381" cy="322" rx="24" ry="3.2" fill="#000000" opacity="0.45" />
<path d="M367 279 L381 279 L379 319 L370 319 Z" fill="#1E3A8A" />
<path d="M382 279 L396 279 L394 319 L385 319 Z" fill="#1B3478" />
<rect x="366" y="316" width="14" height="6" rx="3" fill="#0B1220" />
<rect x="383" y="316" width="14" height="6" rx="3" fill="#0B1220" />
<path d="M366 244 L360 281" stroke="#CBD7EE" strokeWidth="8" strokeLinecap="round" />
<path d="M397 244 L403 281" stroke="#B9C8E6" strokeWidth="8" strokeLinecap="round" />
<circle cx="360" cy="284" r="3.8" fill="#D9A27E" />
<circle cx="403" cy="284" r="3.8" fill="#C98F6B" />
<path d="M365 241 C 371 236, 391 236, 397 241 L 400 282 L 362 282 Z" fill="#DCE6F7" />
<path d="M381 237 C 388 237, 393 238, 397 241 L 400 282 L 381 282 Z" fill="#C3D2EE" />
<path d="M381 240 L381 282" stroke="#AFC1E3" strokeWidth="1.2" />
<path d="M367 243 L 395 276" stroke="#334155" strokeWidth="2.4" />
<rect x="391" y="268" width="13" height="14" rx="2.5" fill="#334155" />
<rect x="377.5" y="230" width="7" height="8" rx="2" fill="#C98F6B" />
<circle cx="371.6" cy="223" r="2.4" fill="#C98F6B" /><circle cx="390.4" cy="223" r="2.4" fill="#C98F6B" />
<ellipse cx="381" cy="221" rx="9" ry="10.5" fill="#111827" />
<path d="M373 216 C 377 211, 386 211, 389 216" stroke="#334155" strokeWidth="1.5" fill="none" />
<path d="M398 242 L401 281" stroke="#93C5FD" strokeWidth="1.2" opacity="0.8" />
</g>
<g fontFamily="Inter, Arial, sans-serif">
<rect x="40" y="118" width="176" height="48" rx="12" fill="#0E1B3D" stroke="#2B4A80" />
<circle cx="62" cy="142" r="10" fill="#14532D" /><path d="M57 145 l3-4 l3 3 l4-6" stroke="#4ADE80" strokeWidth="1.8" fill="none" strokeLinecap="round" />
<text x="80" y="137" fontSize="10" fill="#93C5FD" fontWeight="700" letterSpacing=".5">STEP 1 OF 6</text>
<text x="80" y="155" fontSize="14" fill="#FFFFFF" fontWeight="700">Create your profile</text>
<rect x="250" y="86" width="200" height="48" rx="12" fill="#0E1B3D" stroke="#9A3412" />
<circle cx="272" cy="110" r="10" fill="#431407" /><text x="272" y="114.5" textAnchor="middle" fontSize="12" fontWeight="800" fill="#FB923C">!</text>
<text x="290" y="105" fontSize="10" fill="#FDBA74" fontWeight="700" letterSpacing=".5">NEXT</text>
<text x="290" y="123" fontSize="14" fill="#FFFFFF" fontWeight="700">Add your skills</text>
<rect x="430" y="366" width="210" height="48" rx="12" fill="#0E1B3D" stroke="#2B4A80" />
<circle cx="452" cy="390" r="10" fill="#14532D" /><path d="M447 390 l3 3 l6-7" stroke="#4ADE80" strokeWidth="1.8" fill="none" strokeLinecap="round" />
<text x="470" y="385" fontSize="10" fill="#93C5FD" fontWeight="700" letterSpacing=".5">THEN</text>
<text x="470" y="403" fontSize="14" fill="#FFFFFF" fontWeight="700">Paste a job description</text>
</g>
<rect x="0" y="400" width="760" height="70" fill="url(#r-fade)" />
</svg>
  );
}
