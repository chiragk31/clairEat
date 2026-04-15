import type { Metadata } from 'next';
import Sidebar from '@/components/Sidebar';
import TopBar from '@/components/TopBar';
import WellnessSection from '@/components/WellnessSection';

export const metadata: Metadata = {
  title: 'Wellness — clairEat',
  description: 'Explore wellness tips, health insights, and nutritional guidance tailored to your goals.',
};

const WELLNESS_SECTIONS = [
  {
    icon: 'favorite',
    title: 'Cardiovascular Health',
    description: 'Your heart health is closely linked to your dietary patterns. Prioritize omega-3 rich foods, minimize saturated fats, and stay hydrated. This week, try adding a serving of fatty fish to your meal plan.',
    bgColor: 'bg-rose-50',
    iconColor: 'text-rose-500',
  },
  {
    icon: 'fitness_center',
    title: 'Muscle Recovery',
    description: 'Post-workout nutrition is critical. Aim for 20–40g of protein within 45 minutes of exercise. Greek yogurt, eggs, and lean chicken are excellent recovery foods that align with your current goals.',
    bgColor: 'bg-blue-50',
    iconColor: 'text-blue-500',
  },
  {
    icon: 'bedtime',
    title: 'Sleep & Nutrition',
    description: 'Poor sleep disrupts hunger hormones (ghrelin & leptin), leading to overeating. Your data shows late-night calorie spikes — consider a calming chamomile tea routine after 9 PM instead of snacking.',
    bgColor: 'bg-indigo-50',
    iconColor: 'text-indigo-500',
  },
  {
    icon: 'water_drop',
    title: 'Hydration',
    description: 'You\'re averaging 1.5L of water daily, which is below your 2.5L target. Even mild dehydration reduces cognitive performance by 10–15%. Set hourly reminders and pair water intake with each meal.',
    bgColor: 'bg-sky-50',
    iconColor: 'text-sky-500',
  },
  {
    icon: 'self_improvement',
    title: 'Mindful Eating',
    description: 'Your meal log shows you eat breakfast under 5 minutes on average. Slowing down and chewing thoroughly improves nutrient absorption and reduces overeating by giving your brain time to register fullness.',
    bgColor: 'bg-violet-50',
    iconColor: 'text-violet-500',
  },
  {
    icon: 'eco',
    title: 'Gut Health',
    description: 'A diverse diet fuels a diverse microbiome. This week, try incorporating fermented foods (kimchi, kefir, kombucha) and prebiotic-rich foods (garlic, onion, asparagus) to support your digestive health.',
    bgColor: 'bg-emerald-50',
    iconColor: 'text-emerald-600',
  },
];

const WELLNESS_STATS = [
  { label: 'Avg Sleep',    value: '7.2h', icon: 'bedtime',    color: 'text-indigo-600',  bg: 'bg-indigo-50' },
  { label: 'BMI',          value: '22.4',  icon: 'monitor_weight', color: 'text-emerald-600', bg: 'bg-emerald-50' },
  { label: 'Resting HR',   value: '62bpm', icon: 'favorite',  color: 'text-rose-500',    bg: 'bg-rose-50' },
  { label: 'Stress Level', value: 'Low',   icon: 'self_improvement', color: 'text-violet-600', bg: 'bg-violet-50' },
];

const TIPS = [
  'Eat a rainbow — different coloured vegetables provide different micronutrients.',
  'Batch-cook grains on Sundays to reduce weekday decision fatigue.',
  'Supplement magnesium in the evening to improve sleep quality and muscle recovery.',
  'Drink a glass of water before each meal to naturally reduce portion size.',
];

export default function WellnessPage() {
  return (
    <div className="min-h-screen bg-[#f9faf7]">
      <Sidebar />
      <div className="ml-64 flex flex-col">
        <TopBar placeholder="Search wellness topics..." />

        <main className="px-8 pb-16 pt-8">

          {/* ── Hero header ─────────────────────────── */}
          <div className="mb-12">
            <div className="flex items-center gap-3 mb-4">
              <span className="bg-emerald-100 text-[#006036] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">
                Wellness Hub
              </span>
            </div>
            <h1 className="text-5xl font-bold font-headline text-[#191c1b] tracking-tight leading-tight mb-4">
              Your Wellness <br />
              <span className="text-[#006036] italic">Deep Dive.</span>
            </h1>
            <p className="text-[#3f4941] max-w-xl text-lg">
              Personalized health insights, evidence-based tips, and holistic wellness guidance curated for your unique profile.
            </p>
          </div>

          {/* ── Vital stats strip ───────────────────── */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
            {WELLNESS_STATS.map(stat => (
              <div key={stat.label} className="bg-white rounded-lg p-5 diffusion-shadow flex items-center gap-4">
                <div className={`w-12 h-12 ${stat.bg} rounded-xl flex items-center justify-center shrink-0`}>
                  <span className={`material-symbols-outlined ${stat.color}`} style={{ fontVariationSettings: "'FILL' 1" }}>
                    {stat.icon}
                  </span>
                </div>
                <div>
                  <p className="text-xs font-bold text-[#6f7a70] uppercase tracking-wider">{stat.label}</p>
                  <p className="text-xl font-bold font-headline text-[#191c1b]">{stat.value}</p>
                </div>
              </div>
            ))}
          </div>

          {/* ── Main wellness sections 2x3 grid ──── */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
            {WELLNESS_SECTIONS.map(s => (
              <WellnessSection key={s.title} {...s} />
            ))}
          </div>

          {/* ── Pro tips ─────────────────────────── */}
          <div className="bg-white rounded-lg p-8 diffusion-shadow">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-[#feae2c]/20 rounded-xl flex items-center justify-center">
                <span className="material-symbols-outlined text-[#835500]" style={{ fontVariationSettings: "'FILL' 1" }}>
                  lightbulb
                </span>
              </div>
              <h2 className="text-xl font-bold font-headline text-[#191c1b]">This Week's Pro Tips</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {TIPS.map((tip, i) => (
                <div key={i} className="flex items-start gap-4 p-4 bg-[#f3f4f1] rounded-xl">
                  <div className="w-7 h-7 signature-gradient rounded-full flex items-center justify-center shrink-0 mt-0.5">
                    <span className="text-white text-xs font-bold">{i + 1}</span>
                  </div>
                  <p className="text-sm text-[#3f4941] leading-relaxed">{tip}</p>
                </div>
              ))}
            </div>
          </div>

          {/* ── AI recommendation banner ─────────── */}
          <div className="mt-8 bg-gradient-to-r from-[#006036] to-[#1a7a4a] rounded-xl p-8 text-white flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-white/10 rounded-2xl flex items-center justify-center">
                <span className="material-symbols-outlined text-3xl text-[#9bf6ba]" style={{ fontVariationSettings: "'FILL' 1" }}>
                  psychology
                </span>
              </div>
              <div>
                <p className="text-[#9bf6ba] text-xs font-bold uppercase tracking-widest mb-1">AI Wellness Coach</p>
                <h3 className="text-xl font-bold font-headline">Get a personalized wellness plan</h3>
                <p className="text-white/70 text-sm mt-1">Based on your data, your AI coach has 3 new recommendations ready.</p>
              </div>
            </div>
            <button className="bg-white text-[#006036] px-7 py-3 rounded-full font-bold text-sm hover:opacity-90 transition-opacity whitespace-nowrap diffusion-shadow">
              View Recommendations
            </button>
          </div>
        </main>
      </div>
    </div>
  );
}
