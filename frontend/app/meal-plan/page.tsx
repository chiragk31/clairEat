import type { Metadata } from 'next';
import MealCard from '@/components/MealCard';

export const metadata: Metadata = {
  title: 'Weekly Meal Plan — clairEat',
  description: 'Your personalized AI-generated weekly meal plan with breakdowns for each day.',
};

const DAYS = [
  { label: 'Mon 14', isToday: false },
  { label: 'Tue 15', isToday: false },
  { label: 'Wed 16', isToday: false },
  { label: 'Thu 17', isToday: true },
  { label: 'Fri 18', isToday: false },
  { label: 'Sat 19', isToday: false },
  { label: 'Sun 20', isToday: false },
];

const BREAKFAST = [
  { name: 'Blueberry Overnight Oats', calories: 320, prep: '5m prep', imageEmoji: '🥣' },
  { name: 'Avocado Poached Toast',    calories: 410, prep: '12m prep', imageEmoji: '🥑' },
  { name: 'Greek Honey Bowl',         calories: 280, prep: '3m prep',  imageEmoji: '🍯' },
  { name: 'Protein Pancakes',         calories: 350, prep: '15m prep', imageEmoji: '🥞', isAiPick: true },
  { name: 'Spinach Egg Power Plate',  calories: 210, prep: '10m prep', imageEmoji: '🍳' },
  { name: 'Garden Tofu Scramble',     calories: 330, prep: '20m prep', imageEmoji: '🥬' },
  { name: 'Detox Green Smoothie',     calories: 190, prep: '5m prep',  imageEmoji: '🥤' },
];

const LUNCH = [
  { name: 'Mediterranean Chickpea Salad', calories: 450, prep: '15m prep', imageEmoji: '🥗' },
  { name: 'Quinoa Buddha Bowl',           calories: 520, prep: '25m prep', imageEmoji: '🍚' },
  { name: 'Lemon Herb Chicken Salad',     calories: 380, prep: '20m prep', imageEmoji: '🍋' },
  { name: 'Ahi Tuna Poke Bowl',           calories: 490, prep: '10m prep', imageEmoji: '🐟', isAiPick: true },
  { name: 'Leftover Stir-fry',            calories: 420, prep: '5m prep',  imageEmoji: '🥢' },
  { name: 'Brunch at Café',              calories: 650, prep: 'Eat Out',   imageEmoji: '☕' },
  { name: 'Roast Vegetable Salad',        calories: 340, prep: '45m prep', imageEmoji: '🥕' },
];

const DINNER = [
  { name: 'Pan-Seared Salmon',   calories: 580, prep: '22m prep', imageEmoji: '🐟' },
  { name: 'Whole Grain Pomodoro',calories: 480, prep: '18m prep', imageEmoji: '🍝' },
  { name: 'Turkey Chili',        calories: 510, prep: '35m prep', imageEmoji: '🌶️' },
  { name: 'Steak & Roots',       calories: 620, prep: '30m prep', imageEmoji: '🥩', isAiPick: true },
  { name: 'Tofu Stir-fry',       calories: 410, prep: '25m prep', imageEmoji: '🥦' },
  { name: 'Homemade Pizza',      calories: 750, prep: '45m prep', imageEmoji: '🍕' },
  { name: 'Sunday Roast',        calories: 680, prep: '90m prep', imageEmoji: '🍗' },
];

const MEAL_BG = ['bg-emerald-50','bg-amber-50','bg-sky-50','bg-rose-50','bg-violet-50','bg-orange-50','bg-teal-50'];

export default function MealPlanPage() {
  return (
    <>
      <div className="p-8 max-w-[1600px] mx-auto">
          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-10">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <span className="bg-[#006036]/10 text-[#006036] px-3 py-1 rounded-full text-xs font-bold uppercase">
                  Weekly Plan
                </span>
                <div className="flex items-center gap-2 bg-[#feae2c]/20 text-[#291800] px-3 py-1 rounded-full text-xs font-bold">
                  <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>bolt</span>
                  Target: 2100 kcal
                </div>
              </div>
              <div className="flex items-center gap-3">
                <button className="p-2 hover:bg-[#edeeeb] rounded-full transition-colors text-[#6f7a70]">
                  <span className="material-symbols-outlined">chevron_left</span>
                </button>
                <h1 className="text-4xl font-extrabold font-headline tracking-tight text-[#191c1b]">
                  Week of April 14–20
                </h1>
                <button className="p-2 hover:bg-[#edeeeb] rounded-full transition-colors text-[#6f7a70]">
                  <span className="material-symbols-outlined">chevron_right</span>
                </button>
              </div>
            </div>

            <button className="flex items-center gap-3 px-7 py-4 rounded-full font-bold text-white shadow-lg shadow-[#006036]/20 bg-gradient-to-br from-[#006036] to-[#1a7a4a] hover:opacity-90 active:scale-95 transition-all">
              <span>Generate New Plan with AI</span>
              <span className="material-symbols-outlined text-xl" style={{ fontVariationSettings: "'FILL' 1" }}>auto_awesome</span>
            </button>
          </div>

          {/* ── 7-column meal grid ── */}
          <div className="overflow-x-auto">
            <div className="min-w-[900px]">
              {/* Day headers */}
              <div className="grid grid-cols-7 gap-3 mb-4">
                {DAYS.map(d => (
                  <div key={d.label} className="text-center pb-2">
                    <p className={`text-xs font-bold uppercase tracking-widest ${d.isToday ? 'text-[#006036]' : 'text-[#6f7a70]'}`}>
                      {d.label}
                    </p>
                    {d.isToday && <div className="w-1 h-1 bg-[#006036] rounded-full mx-auto mt-1" />}
                  </div>
                ))}
              </div>

              {/* Meal rows */}
              {[
                { label: 'Breakfast', meals: BREAKFAST },
                { label: 'Lunch',     meals: LUNCH },
                { label: 'Dinner',    meals: DINNER },
              ].map(row => (
                <div key={row.label} className="mb-6">
                  <div className="text-[10px] font-bold text-[#6f7a70]/60 uppercase tracking-[0.2em] mb-2 pl-1">
                    {row.label}
                  </div>
                  <div className="grid grid-cols-7 gap-3">
                    {row.meals.map((meal, i) => (
                      <div key={i} className={DAYS[i].isToday ? 'relative' : ''}>
                        {DAYS[i].isToday && (
                          <div className="absolute -inset-1.5 bg-[#006036]/5 rounded-xl border border-[#006036]/10 -z-10" />
                        )}
                        <MealCard {...meal} bgColor={MEAL_BG[i % MEAL_BG.length]} />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
      </div>
    </>
  );
}
