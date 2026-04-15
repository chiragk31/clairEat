import type { Metadata } from 'next';
import Sidebar from '@/components/Sidebar';
import TopBar from '@/components/TopBar';
import DashboardCard from '@/components/DashboardCard';

export const metadata: Metadata = {
  title: 'Analytics — clairEat',
  description: 'Deep dive into your nutritional velocity, macro breakdown, and habit consistency.',
};

/* ─── Calorie chart data ─────────────────────────────── */
const CALORIE_DOTS = [
  { day: 'MON', pct: 40 },
  { day: 'TUE', pct: 55 },
  { day: 'WED', pct: 48 },
  { day: 'THU', pct: 70 },
  { day: 'FRI', pct: 62 },
  { day: 'SAT', pct: 35 },
  { day: 'SUN', pct: 50 },
];

const MACRO_BARS = [
  { day: 'M', protein: 30, carbs: 45, fat: 25, heightPct: 80 },
  { day: 'T', protein: 25, carbs: 50, fat: 25, heightPct: 100 },
  { day: 'W', protein: 40, carbs: 35, fat: 25, heightPct: 60 },
  { day: 'T', protein: 35, carbs: 40, fat: 25, heightPct: 90 },
  { day: 'F', protein: 30, carbs: 40, fat: 30, heightPct: 85 },
  { day: 'S', protein: 20, carbs: 60, fat: 20, heightPct: 50 },
  { day: 'S', protein: 35, carbs: 40, fat: 25, heightPct: 75 },
];

const FAVORITES = [
  { name: 'Avocado Toast',         count: '4 times', pct: 80 },
  { name: 'Grilled Chicken Salad', count: '3 times', pct: 60 },
  { name: 'Almond Butter',         count: '3 times', pct: 60 },
  { name: 'Blueberry Smoothie',    count: '2 times', pct: 40 },
];

const INSIGHTS = [
  {
    title: 'Protein Deficit',
    description: 'You are 15g below your protein goal on average. Consider adding Greek yogurt to your breakfast.',
    icon: 'lightbulb',
    iconBg: 'bg-primary/10',
    iconColor: 'text-primary',
    border: 'border-primary',
  },
  {
    title: 'Late Night Spike',
    description: 'Most sugar intake happens after 9 PM. Swapping late snacks for tea could improve sleep quality.',
    icon: 'bedtime',
    iconBg: 'bg-[#835500]/10',
    iconColor: 'text-[#835500]',
    border: 'border-[#835500]',
  },
  {
    title: 'Energy Patterns',
    description: 'Consistency is high! You\'ve logged meals at the same time for 5 days straight. Keep it up.',
    icon: 'trending_up',
    iconBg: 'bg-[#1a7a4a]/10',
    iconColor: 'text-[#1a7a4a]',
    border: 'border-[#1a7a4a]',
  },
];

/* 90-day heatmap rows (static mock data) */
const HEATMAP_ROWS = [
  ['full','70','20','empty','40','full','full','70','full','40','full','70','20'],
  ['40','full','70','40','empty','20','70','full','20','70','40','full','70'],
  ['empty','20','40','70','full','full','70','40','empty','20','full','70','40'],
  ['70','full','70','40','20','empty','40','70','full','70','40','20','full'],
  ['20','40','70','full','full','70','40','20','empty','20','40','70','full'],
];

function heatCell(val: string) {
  const map: Record<string,string> = {
    full: 'bg-[#006036]', '70': 'bg-[#006036]/70', '40': 'bg-[#006036]/40',
    '20': 'bg-[#006036]/20', empty: 'bg-[#edeeeb]',
  };
  return map[val] ?? 'bg-[#edeeeb]';
}

export default function AnalyticsPage() {
  return (
    <div className="min-h-screen bg-[#f9faf7]">
      <Sidebar />
      <div className="ml-64 flex flex-col">
        <TopBar placeholder="Search analytics..." />

        <main className="px-8 pb-12 pt-8">
          {/* ── Header ──────────────────────────────────── */}
          <div className="flex flex-col md:flex-row justify-between items-end gap-6 mb-12">
            <div>
              <h1 className="text-5xl font-bold font-headline text-[#191c1b] tracking-tight leading-tight">
                Your Health <br />
                <span className="text-[#006036] italic">Deep Dive.</span>
              </h1>
              <p className="text-[#3f4941] mt-2 max-w-md">
                Detailed insights into your nutritional velocity and habit consistency over the last 7 days.
              </p>
            </div>

            {/* Streak widget */}
            <div className="bg-white diffusion-shadow p-6 rounded-lg flex items-center gap-8 border border-[#bec9be]/10">
              <div className="text-center">
                <p className="text-[10px] text-[#6f7a70] uppercase tracking-wider mb-1">Current Streak</p>
                <div className="flex items-center justify-center gap-1">
                  <span className="text-3xl font-bold font-headline text-[#835500]">12</span>
                  <span className="material-symbols-outlined text-[#835500] text-2xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                    local_fire_department
                  </span>
                </div>
              </div>
              <div className="w-px h-10 bg-[#bec9be]/30" />
              <div className="text-center">
                <p className="text-[10px] text-[#6f7a70] uppercase tracking-wider mb-1">Longest Streak</p>
                <div className="flex items-center justify-center gap-1">
                  <span className="text-3xl font-bold font-headline text-[#006036]">30</span>
                  <span className="material-symbols-outlined text-[#006036] text-2xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                    emoji_events
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* ── Grid ────────────────────────────────────── */}
          <div className="grid grid-cols-12 gap-6">

            {/* Calorie Velocity chart */}
            <div className="col-span-12 lg:col-span-8 bg-white diffusion-shadow rounded-lg p-8">
              <div className="flex justify-between items-start mb-8">
                <div>
                  <h3 className="text-lg font-bold font-headline text-[#191c1b]">Calorie Velocity</h3>
                  <p className="text-xs text-[#6f7a70]">Target: 2,400 kcal/day</p>
                </div>
                <div className="bg-[#1a7a4a]/10 px-3 py-1 rounded-full text-[#006036] text-xs font-bold">
                  +4% vs last week
                </div>
              </div>

              {/* Line chart mock */}
              <div className="relative h-64 w-full flex items-end justify-between gap-2 border-b border-[#bec9be]/20 pb-4">
                {/* Grid lines */}
                <div className="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-10">
                  <div className="border-t border-[#6f7a70]" /><div className="border-t border-[#6f7a70]" />
                  <div className="border-t border-[#6f7a70]" />
                </div>
                {CALORIE_DOTS.map((dot, i) => (
                  <div key={i} className="group relative flex-1 flex flex-col items-center justify-end h-full">
                    <div
                      className="w-3 h-3 rounded-full bg-[#006036] border-2 border-white absolute shadow-sm"
                      style={{ bottom: `${dot.pct}%` }}
                    />
                    <div className="text-[10px] text-[#6f7a70] font-bold mt-2 absolute bottom-0 translate-y-6">{dot.day}</div>
                  </div>
                ))}
                <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 700 256">
                  <path
                    d="M50,154 L150,115 L250,133 L350,77 L450,97 L550,166 L650,128"
                    fill="none" stroke="#006036" strokeLinecap="round" strokeWidth="3"
                  />
                  <path
                    d="M50,154 L150,115 L250,133 L350,77 L450,97 L550,166 L650,128 L650,256 L50,256 Z"
                    fill="url(#grad)" opacity="0.08"
                  />
                  <defs>
                    <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#006036" />
                      <stop offset="100%" stopColor="transparent" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
            </div>

            {/* AI Insights */}
            <div className="col-span-12 lg:col-span-4 flex flex-col gap-4">
              {INSIGHTS.map(ins => (
                <DashboardCard key={ins.title} {...ins} />
              ))}
            </div>

            {/* Weekly Macros stacked bar */}
            <div className="col-span-12 lg:col-span-6 bg-white diffusion-shadow rounded-lg p-8">
              <div className="flex justify-between items-center mb-8">
                <h3 className="text-lg font-bold font-headline text-[#191c1b]">Weekly Macros</h3>
                <div className="flex gap-4">
                  {[
                    { label: 'P', color: 'bg-[#006036]' },
                    { label: 'C', color: 'bg-[#1a7a4a]' },
                    { label: 'F', color: 'bg-[#feae2c]' },
                  ].map(l => (
                    <div key={l.label} className="flex items-center gap-1.5">
                      <div className={`w-2 h-2 rounded-full ${l.color}`} />
                      <span className="text-[10px] font-bold text-[#6f7a70]">{l.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-between items-end h-48 gap-3">
                {MACRO_BARS.map((bar, i) => (
                  <div key={i} className="flex-1 flex flex-col gap-1 items-center h-full justify-end">
                    <div
                      className="w-full flex flex-col-reverse rounded-sm overflow-hidden"
                      style={{ height: `${bar.heightPct}%` }}
                    >
                      <div className="bg-[#006036]" style={{ height: `${bar.protein}%` }} />
                      <div className="bg-[#1a7a4a]" style={{ height: `${bar.carbs}%` }} />
                      <div className="bg-[#feae2c]" style={{ height: `${bar.fat}%` }} />
                    </div>
                    <span className="text-[10px] text-[#6f7a70] font-bold">{bar.day}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Weekly Favorites */}
            <div className="col-span-12 lg:col-span-6 bg-white diffusion-shadow rounded-lg p-8">
              <h3 className="text-lg font-bold font-headline text-[#191c1b] mb-8">Weekly Favorites</h3>
              <div className="space-y-5">
                {FAVORITES.map(fav => (
                  <div key={fav.name} className="space-y-2">
                    <div className="flex justify-between text-xs font-bold text-[#3f4941]">
                      <span>{fav.name}</span>
                      <span>{fav.count}</span>
                    </div>
                    <div className="w-full h-2 bg-[#edeeeb] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#006036] rounded-full transition-all"
                        style={{ width: `${fav.pct}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Heatmap */}
            <div className="col-span-12 bg-white diffusion-shadow rounded-lg p-8">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <div>
                  <h3 className="text-lg font-bold font-headline text-[#191c1b]">Consistency Grid</h3>
                  <p className="text-xs text-[#6f7a70]">Past 90 days of ritual adherence</p>
                </div>
                <div className="flex items-center gap-2 text-[10px] text-[#6f7a70] font-bold">
                  <span>Less</span>
                  {['bg-[#edeeeb]','bg-[#006036]/20','bg-[#006036]/40','bg-[#006036]/70','bg-[#006036]'].map((c,i) => (
                    <div key={i} className={`w-3 h-3 rounded-sm ${c}`} />
                  ))}
                  <span>More</span>
                </div>
              </div>
              <div className="overflow-x-auto pb-2">
                <div className="flex flex-col gap-1 min-w-[600px]">
                  {HEATMAP_ROWS.map((row, ri) => (
                    <div key={ri} className="flex gap-1">
                      {row.map((cell, ci) => (
                        <div key={ci} className={`w-3 h-3 rounded-sm ${heatCell(cell)}`} />
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* AI FAB */}
      <div className="fixed bottom-8 right-8 z-50">
        <button className="w-16 h-16 rounded-full bg-[#006036] flex items-center justify-center text-white diffusion-shadow border-4 border-[#1a7a4a]/20 group relative">
          <span className="material-symbols-outlined text-3xl">psychology</span>
          <span className="absolute -top-10 right-0 bg-white text-[#191c1b] text-[10px] font-bold px-3 py-1 rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
            Ask Coach
          </span>
        </button>
      </div>
    </div>
  );
}
