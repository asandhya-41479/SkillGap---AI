import { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Logo from './Logo';

// One shared shell for every logged-in page: sidebar on desktop, bottom tab bar on phones/tablets.
const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z' },
  { to: '/skills', label: 'My Skills', icon: 'M12 3l9 5-9 5-9-5 9-5zM3 13l9 5 9-5' },
  { to: '/jobs', label: 'Job Intelligence', icon: 'M3 7h18v13H3zM8 7V5a2 2 0 012-2h4a2 2 0 012 2v2' },
  { to: '/skill-gap', label: 'Skill Gap', icon: 'M12 3a9 9 0 100 18 9 9 0 000-18zM12 8a4 4 0 100 8 4 4 0 000-8z' },
  { to: '/roadmap', label: 'Roadmap', icon: 'M9 4L3 6v14l6-2 6 2 6-2V4l-6 2-6-2zM9 4v14M15 6v14' },
  { to: '/readiness', label: 'Progress & Readiness', icon: 'M3 17l6-6 4 4 8-8M15 7h6v6' },
  { to: '/career', label: 'Career Intelligence', icon: 'M12 3a9 9 0 100 18 9 9 0 000-18zM15.5 8.5l-2 5-5 2 2-5 5-2z' },
  { to: '/settings', label: 'Settings', icon: 'M12 9a3 3 0 100 6 3 3 0 000-6zM19.4 15a1.7 1.7 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-2.9 1.2V21a2 2 0 11-4 0v-.1a1.7 1.7 0 00-2.9-1.2l-.1.1a2 2 0 11-2.8-2.8l.1-.1A1.7 1.7 0 003 15H3a2 2 0 110-4h.1a1.7 1.7 0 001.2-2.9l-.1-.1a2 2 0 112.8-2.8l.1.1A1.7 1.7 0 009 3.1V3a2 2 0 114 0v.1a1.7 1.7 0 002.9 1.2l.1-.1a2 2 0 112.8 2.8l-.1.1A1.7 1.7 0 0021 11h.1a2 2 0 110 4H21a1.7 1.7 0 00-1.6 0z' },
];

function Icon({ d }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={d} />
    </svg>
  );
}

function navClass({ isActive }) {
  return [
    'flex min-h-11 shrink-0 items-center gap-3 rounded-xl px-3.5 text-sm font-medium transition',
    isActive ? 'bg-brand text-white shadow-[0_6px_16px_rgba(37,99,235,.35)]' : 'text-slate-300 hover:bg-white/10 hover:text-white',
  ].join(' ');
}

// Phone tab bar: 4 main pages + "More" (the rest of the menu).
const TABS = ['/dashboard', '/skills', '/skill-gap', '/roadmap'];
const SHORT = { '/dashboard': 'Home', '/skills': 'Skills', '/skill-gap': 'Gap', '/roadmap': 'Roadmap' };

export default function AppLayout() {
  const { user, fetchCurrentUser, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [moreOpen, setMoreOpen] = useState(false);

  useEffect(() => { setMoreOpen(false); }, [location.pathname]);

  useEffect(() => {
    if (!user) {
      fetchCurrentUser().catch(() => {
        logout();
        navigate('/login');
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const initial = (user?.name || '?').trim().charAt(0).toUpperCase();

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[256px_1fr]">
      {/* Sidebar (desktop) */}
      <aside className="hidden bg-navy px-4 py-6 lg:sticky lg:top-0 lg:flex lg:h-screen lg:flex-col">
        <div className="px-2 pb-8"><Logo /></div>
        <nav aria-label="Main" className="flex flex-col gap-1">
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to} className={navClass}>
              <Icon d={n.icon} />{n.label}
            </NavLink>
          ))}
        </nav>
        <button type="button" onClick={handleLogout}
          className="mt-auto flex min-h-11 items-center gap-3 rounded-xl px-3.5 text-sm font-medium text-slate-300 hover:bg-white/10 hover:text-white">
          <Icon d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4M10 17l5-5-5-5M15 12H3" />Log out
        </button>
      </aside>

      <div className="min-w-0">
        {/* Top bar */}
        <header className="sticky top-0 z-20 border-b border-line bg-white/90 backdrop-blur">
          <div className="flex items-center justify-between gap-4 px-4 py-3 sm:px-8">
            <div className="lg:hidden"><Logo dark /></div>
            <div className="hidden items-center gap-2 lg:flex">
              {user?.target_role && (
                <span className="inline-flex items-center gap-2 rounded-full bg-brand-soft px-3 py-1.5 text-sm font-semibold text-brand-dark">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" aria-hidden="true"><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="4" /></svg>
                  Target: {user.target_role}
                </span>
              )}
            </div>
            <div className="flex items-center gap-3">
              <span className="hidden text-sm font-semibold text-ink sm:block">{user?.name}</span>
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand font-display text-sm font-bold text-white" aria-hidden="true">{initial}</span>
                          </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1280px] px-4 pb-28 pt-6 sm:px-8 sm:pt-8 lg:pb-10">
          <Outlet />
        </main>
      </div>

      {/* Phone / tablet: "More" sheet + bottom tab bar */}
      {moreOpen && (
        <div className="fixed inset-0 z-30 bg-slate-900/40 lg:hidden" onClick={() => setMoreOpen(false)} aria-hidden="true" />
      )}
      {moreOpen && (
        <nav aria-label="More pages" id="more-menu"
          className="fixed inset-x-3 bottom-20 z-40 flex flex-col gap-1 rounded-2xl bg-navy p-3 shadow-2xl lg:hidden">
          {NAV.filter((n) => !TABS.includes(n.to)).map((n) => (
            <NavLink key={n.to} to={n.to} className={navClass}><Icon d={n.icon} />{n.label}</NavLink>
          ))}
          <button type="button" onClick={handleLogout}
            className="flex min-h-11 items-center gap-3 rounded-xl px-3.5 text-sm font-medium text-slate-300 hover:bg-white/10 hover:text-white">
            <Icon d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4M10 17l5-5-5-5M15 12H3" />Log out
          </button>
        </nav>
      )}
      <nav aria-label="Main" className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-5 border-t border-line bg-white pb-[env(safe-area-inset-bottom)] lg:hidden">
        {NAV.filter((n) => TABS.includes(n.to)).map((n) => (
          <NavLink key={n.to} to={n.to}
            className={({ isActive }) => `flex min-h-16 flex-col items-center justify-center gap-1 text-[11px] font-semibold ${isActive ? 'text-brand' : 'text-slate-600'}`}>
            <Icon d={n.icon} />{SHORT[n.to]}
          </NavLink>
        ))}
        <button type="button" onClick={() => setMoreOpen((o) => !o)} aria-expanded={moreOpen} aria-controls="more-menu"
          className={`flex min-h-16 flex-col items-center justify-center gap-1 text-[11px] font-semibold ${moreOpen ? 'text-brand' : 'text-slate-600'}`}>
          <Icon d="M4 6h16M4 12h16M4 18h16" />More
        </button>
      </nav>
    </div>
  );
}
