'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

/* ─── Nav items config ─────────────────────────────────────── */
const navItems = [
  { href: '/',           icon: 'dashboard',        label: 'Dashboard' },
  { href: '/log-meal',   icon: 'add_a_photo',       label: 'Log Meal' },
  { href: '/meal-plan',  icon: 'restaurant_menu',   label: 'Meal Plan' },
  { href: '/ai-coach',   icon: 'psychology',        label: 'AI Coach' },
  { href: '/analytics',  icon: 'leaderboard',       label: 'Analytics' },
  { href: '/wellness',   icon: 'favorite',          label: 'Wellness' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-full flex flex-col py-8 px-4 bg-emerald-50/50 backdrop-blur-xl w-64 border-r border-stone-200/50 z-50">
      {/* Brand */}
      <div className="mb-12 px-4">
        <h1 className="text-2xl font-bold tracking-tight text-emerald-900 font-headline">clairEat</h1>
        <p className="text-[10px] uppercase tracking-widest text-stone-500 font-bold mt-1">Premium Wellness</p>
      </div>

      {/* Nav links */}
      <nav className="flex-1 space-y-1">
        {navItems.map(({ href, icon, label }) => {
          const isActive = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 font-medium ${
                isActive
                  ? 'text-emerald-900 border-l-4 border-emerald-700 font-bold bg-emerald-100/50 translate-x-1'
                  : 'text-stone-500 hover:text-emerald-800 hover:bg-emerald-50'
              }`}
            >
              <span
                className="material-symbols-outlined"
                style={isActive ? { fontVariationSettings: "'FILL' 1" } : {}}
              >
                {icon}
              </span>
              <span>{label}</span>
            </Link>
          );
        })}

        {/* Settings at bottom */}
        <Link
          href="/settings"
          className="flex items-center gap-3 px-4 py-3 rounded-xl transition-colors text-stone-500 hover:text-emerald-800 hover:bg-emerald-50 mt-8"
        >
          <span className="material-symbols-outlined">settings</span>
          <span>Settings</span>
        </Link>
      </nav>

      {/* User profile footer */}
      <div className="mt-auto px-4 flex items-center gap-3 pt-6 border-t border-stone-200/50">
        <div className="w-10 h-10 rounded-full bg-emerald-200 flex items-center justify-center text-emerald-900 font-bold text-sm">
          AR
        </div>
        <div>
          <p className="text-sm font-bold text-on-surface">Alex Rivera</p>
          <p className="text-[10px] text-stone-500 uppercase font-bold tracking-tighter">Premium Member</p>
        </div>
      </div>
    </aside>
  );
}
