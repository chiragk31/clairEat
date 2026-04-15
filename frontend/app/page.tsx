import type { Metadata } from 'next';
import SummaryCard from '@/components/SummaryCard';
import { Card } from '@/components/ui/Card';
export const metadata: Metadata = {
  title: 'Dashboard — clairEat',
  description: 'Your personalized nutrition dashboard with daily tracking, meal logs, and AI insights.',
};

/* ─── Static meal data (swap for API call) ─── */
const MEALS = [
  {
    id: 'breakfast',
    label: 'Breakfast',
    icon: 'coffee',
    iconBg: 'bg-emerald-50',
    iconColor: 'text-primary',
    detail: 'Oats with Berries, Espresso',
    kcal: '420 kcal',
    time: '08:30 AM',
    logged: true,
  },
  {
    id: 'lunch',
    label: 'Lunch',
    icon: 'lunch_dining',
    iconBg: 'bg-amber-50',
    iconColor: 'text-secondary',
    detail: 'Grilled Chicken Salad, Quinoa',
    kcal: '680 kcal',
    time: '01:15 PM',
    logged: true,
  },
  {
    id: 'dinner',
    label: 'Dinner',
    icon: 'dinner_dining',
    iconBg: 'bg-stone-100',
    iconColor: 'text-on-surface-variant',
    detail: 'Not logged yet',
    kcal: null,
    time: null,
    logged: false,
  },
  {
    id: 'snacks',
    label: 'Snacks',
    icon: 'cookie',
    iconBg: 'bg-rose-50',
    iconColor: 'text-[#8b373f]',
    detail: 'Almonds (20g)',
    kcal: '140 kcal',
    time: '04:00 PM',
    logged: true,
  },
];

const MACROS = [
  { label: 'Protein', val: '62g', pct: 45, color: 'bg-primary' },
  { label: 'Carbs',   val: '145g', pct: 70, color: 'bg-[#feae2c]' },
  { label: 'Fat',     val: '38g',  pct: 30, color: 'bg-on-surface-variant' },
];

const WEEK_DAYS = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];

export default function DashboardPage() {
  return (
    <div className="w-full">
      <main className="px-4 md:px-8 pt-8 grid grid-cols-12 gap-8">

          {/* ── Center: Tracking & Meals ─────────────────── */}
          <div className="col-span-12 lg:col-span-8 space-y-10">

            {/* Greeting */}
            <div className="flex justify-between items-end">
              <div>
                <h1 className="text-3xl font-bold font-headline text-on-surface tracking-tight">
                  Good morning, Chirag 👋
                </h1>
                <p className="text-on-surface-variant font-medium mt-1">Tuesday, April 14</p>
              </div>
              <div className="flex items-center gap-3 bg-[#f3f4f1] px-5 py-3 rounded-lg">
                <span className="material-symbols-outlined text-[#835500]" style={{ fontVariationSettings: "'FILL' 1" }}>
                  sunny
                </span>
                <div className="text-right">
                  <p className="text-sm font-bold text-[#191c1b]">32°C</p>
                  <p className="text-[10px] text-[#3f4941] uppercase tracking-wider">Mumbai</p>
                </div>
              </div>
            </div>

            {/* Bento summary grid */}
            <div className="grid grid-cols-3 gap-6">
              {/* Calorie ring card */}
              <Card variant="elevated" className="col-span-2 flex items-center justify-between">
                <div className="space-y-6 flex-1">
                  <div>
                    <h3 className="text-on-surface-variant text-sm font-medium">Daily Energy</h3>
                    <div className="flex items-baseline gap-2 mt-2">
                       <span className="text-4xl font-bold text-on-surface font-headline">1,240</span>
                       <span className="text-on-surface-variant">/ 2,100 kcal</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4 pt-4">
                    {MACROS.map(m => (
                      <div key={m.label} className="space-y-2">
                         <p className="text-[10px] font-bold text-on-surface-variant uppercase">{m.label}</p>
                         <div className="h-1.5 bg-surface-container rounded-full overflow-hidden">
                           <div className={`h-full ${m.color} rounded-full`} style={{ width: `${m.pct}%` }} />
                         </div>
                         <p className="text-xs font-semibold">{m.val}</p>
                      </div>
                    ))}
                  </div>
                </div>
                {/* Radial progress */}
                <div className="relative w-40 h-40 flex items-center justify-center shrink-0">
                  <svg className="w-full h-full transform -rotate-90">
                     <circle className="text-surface-container-high" cx="80" cy="80" fill="transparent" r="70" stroke="currentColor" strokeWidth="12" />
                     <circle
                       className="text-primary"
                       cx="80" cy="80" fill="transparent" r="70"
                       stroke="currentColor"
                       strokeDasharray="440"
                       strokeDashoffset="180"
                       strokeLinecap="round"
                       strokeWidth="12"
                     />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                     <span className="text-2xl font-bold font-headline">59%</span>
                     <span className="text-[10px] text-on-surface-variant font-bold uppercase">Done</span>
                  </div>
                </div>
              </Card>

              {/* Featured card */}
              <Card variant="filled" className="bg-primary/90 text-white relative overflow-hidden flex flex-col justify-end p-6 border-none">
                <div className="absolute inset-0 opacity-20 bg-gradient-to-br from-primary-fixed to-primary" />
                <div className="relative z-10">
                   <span className="text-[10px] font-bold uppercase tracking-widest text-primary-fixed">Featured Guide</span>
                   <h4 className="text-xl font-bold font-headline leading-tight mt-2">Optimal Post-Workout Macros</h4>
                   <button className="mt-4 text-xs font-bold flex items-center gap-2 hover:translate-x-1 transition-transform truncate text-white">
                     Read Article <span className="material-symbols-outlined text-sm">arrow_forward</span>
                   </button>
                </div>
              </Card>
            </div>

            {/* Meals section */}
            <section className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold font-headline tracking-tight text-[#191c1b]">Today's Meals</h2>
                <button className="text-[#006036] font-bold text-sm flex items-center gap-1 hover:opacity-70 transition-opacity">
                  <span className="material-symbols-outlined text-lg">calendar_today</span>
                  Past 7 Days
                </button>
              </div>

              <div className="space-y-4">
                {MEALS.map(meal => (
                  <Card
                    key={meal.id}
                    variant="elevated"
                    padding="sm"
                    className="group hover:shadow-md transition-all flex items-center justify-between"
                  >
                    <div className="flex items-center gap-4">
                       <div className={`w-12 h-12 rounded-lg ${meal.iconBg} flex items-center justify-center ${meal.iconColor}`}>
                         <span className="material-symbols-outlined">{meal.icon}</span>
                       </div>
                       <div>
                         <h4 className="font-bold text-on-surface">{meal.label}</h4>
                         <p className={`text-xs ${meal.logged ? 'text-on-surface-variant' : 'text-outline italic'}`}>
                           {meal.logged ? `Logged: ${meal.detail}` : meal.detail}
                         </p>
                       </div>
                    </div>
                    <div className="flex items-center gap-5">
                       {meal.logged ? (
                         <>
                           <div className="text-right">
                             <p className="text-sm font-bold text-on-surface">{meal.kcal}</p>
                             <p className="text-[10px] text-on-surface-variant uppercase font-bold">{meal.time}</p>
                           </div>
                           <button className="w-8 h-8 rounded-full border border-outline-variant flex items-center justify-center text-primary hover:bg-primary hover:text-white transition-colors">
                             <span className="material-symbols-outlined text-lg">add</span>
                           </button>
                         </>
                       ) : (
                         <button className="px-4 py-1.5 signature-gradient text-white text-xs font-bold rounded-full">
                           + Add Meal
                         </button>
                       )}
                    </div>
                  </Card>
                ))}
              </div>
            </section>
          </div>

          {/* ── Right Sidebar ──────────────────────────── */}
          <div className="col-span-12 lg:col-span-4 space-y-7">
            {/* AI Insight */}
            <div className="bg-white/80 backdrop-blur-md rounded-lg p-6 border border-[#006036]/10 relative overflow-hidden diffusion-shadow">
              <div className="absolute top-0 right-0 p-4 opacity-5">
                <span className="material-symbols-outlined text-6xl">psychology</span>
              </div>
              <div className="flex items-center gap-2 text-[#006036] font-bold text-xs uppercase tracking-widest mb-4">
                <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>lightbulb</span>
                AI Coach Insight
              </div>
              <p className="text-[#191c1b] font-headline font-semibold text-base leading-snug">
                "You've been skipping protein at breakfast this week. Try adding Greek yogurt to reach your muscle recovery goal."
              </p>
              <div className="mt-6 flex gap-3">
                <button className="bg-[#abffc6] text-[#006036] px-4 py-2 rounded-md text-xs font-bold hover:opacity-90 transition-opacity">
                  See Options
                </button>
                <button className="text-[#3f4941] text-xs font-bold px-2 py-2">Dismiss</button>
              </div>
            </div>

            {/* Water tracker */}
            <div className="bg-[#f3f4f1] rounded-lg p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-bold text-[#191c1b]">Water Tracker</h3>
                <span className="text-[#006036] font-bold text-sm">1.5 / 2L</span>
              </div>
              <div className="grid grid-cols-4 gap-3">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="aspect-[2/3] bg-blue-400/60 rounded-sm" />
                ))}
                <div className="aspect-[2/3] bg-[#e7e8e6] rounded-sm border-2 border-dashed border-[#bec9be] flex items-center justify-center cursor-pointer hover:border-[#006036] transition-colors">
                  <span className="material-symbols-outlined text-[#bec9be] text-sm">add</span>
                </div>
                <div className="aspect-[2/3] bg-[#e7e8e6] rounded-sm border-2 border-dashed border-[#bec9be]" />
              </div>
              <p className="text-[10px] text-[#3f4941] mt-4 text-center font-bold uppercase tracking-widest">6 of 8 glasses logged</p>
            </div>

            {/* Streak card */}
            <div className="bg-white rounded-lg p-6 flex items-center gap-4 border border-stone-100 diffusion-shadow">
              <div className="w-14 h-14 bg-[#ffddb4] rounded-full flex items-center justify-center text-[#835500]">
                <span className="material-symbols-outlined text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                  local_fire_department
                </span>
              </div>
              <div>
                <h3 className="font-bold text-[#191c1b]">12-Day Streak 🔥</h3>
                <p className="text-xs text-[#3f4941] mt-0.5">Keep logging to reach your 14-day reward!</p>
              </div>
            </div>

            {/* Weekly progress dots */}
            <div className="bg-white rounded-lg p-6 border border-stone-100 diffusion-shadow">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-bold text-sm text-[#191c1b]">Weekly Progress</h3>
                <span className="material-symbols-outlined text-sm text-[#6f7a70]">more_horiz</span>
              </div>
              <div className="flex justify-between">
                {WEEK_DAYS.map((d, i) => (
                  <div key={i} className="flex flex-col items-center gap-2">
                    <span className={`text-[10px] font-bold uppercase ${i === 1 ? 'text-[#006036]' : 'text-[#3f4941]'}`}>{d}</span>
                    <div
                      className={`rounded-full ${
                        i < 2 ? 'w-3 h-3 bg-[#006036]' : 'w-2 h-2 bg-[#e2e3e0]'
                      } ${i === 1 ? 'ring-4 ring-emerald-50' : ''}`}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </main>
      {/* AI FAB */}
      <button className="fixed bottom-8 right-8 w-14 h-14 md:w-16 md:h-16 signature-gradient text-white rounded-full shadow-2xl flex items-center justify-center hover:scale-105 transition-transform group z-50">
        <span className="material-symbols-outlined text-2xl md:text-3xl group-hover:rotate-12 transition-transform">auto_awesome</span>
      </button>
    </div>
  );
}
