'use client';

import { useState } from 'react';

const MEAL_TYPES = ['Breakfast', 'Lunch', 'Dinner', 'Snack', 'Pre-Workout', 'Post-Workout'];
const MOODS = ['😊', '😐', '😴', '😓'];
const FOODS = [
  { name: 'Avocado Sourdough Toast', cal: 245, unit: '100g', icon: 'restaurant' },
  { name: 'Large Poached Egg', cal: 155, unit: '100g', icon: 'egg_alt' },
  { name: 'Black Coffee', cal: 2, unit: '100g', icon: 'coffee' },
];

interface LoggedItem {
  name: string;
  qty: number;
  cal: number;
}

export default function MealForm() {
  const [mealType, setMealType] = useState('Breakfast');
  const [searchQuery, setSearchQuery] = useState('');
  const [mood, setMood] = useState('😐');
  const [hunger, setHunger] = useState(4);
  const [notes, setNotes] = useState('');
  const [loggedItems, setLoggedItems] = useState<LoggedItem[]>([
    { name: 'Organic Blueberries', qty: 125, cal: 71 },
    { name: 'Greek Yogurt (Full Fat)', qty: 200, cal: 194 },
  ]);
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const totalCal = loggedItems.reduce((sum, item) => sum + item.cal, 0);

  const handleAdd = (food: typeof FOODS[0]) => {
    setLoggedItems(prev => [...prev, { name: food.name, qty: 100, cal: food.cal }]);
  };

  const handleQtyChange = (index: number, qty: number) => {
    setLoggedItems(prev =>
      prev.map((it, i) => (i === index ? { ...it, qty } : it))
    );
  };

  const handleSubmit = async () => {
    if (loggedItems.length === 0) return;
    setLoading(true);
    // Simulated API call — ready for backend integration
    await new Promise(r => setTimeout(r, 1200));
    setLoading(false);
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="w-20 h-20 signature-gradient rounded-full flex items-center justify-center mb-6 shadow-lg">
          <span className="material-symbols-outlined text-white text-4xl" style={{ fontVariationSettings: "'FILL' 1" }}>
            check_circle
          </span>
        </div>
        <h2 className="text-2xl font-bold font-headline text-[#191c1b] mb-2">Entry Saved!</h2>
        <p className="text-[#6f7a70] mb-8">Your meal has been logged successfully.</p>
        <button
          onClick={() => { setSubmitted(false); setLoggedItems([]); }}
          className="signature-gradient text-white px-8 py-3 rounded-full font-bold hover:opacity-90 transition-opacity"
        >
          Log Another Meal
        </button>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-12 gap-8">
      {/* ── Left: Search & Discovery ────────────────────────── */}
      <div className="col-span-12 lg:col-span-7 space-y-8">
        {/* Meal type selector */}
        <div className="bg-[#f3f4f1] p-2 rounded-2xl flex flex-wrap gap-2">
          {MEAL_TYPES.map(type => (
            <button
              key={type}
              onClick={() => setMealType(type)}
              className={`flex-1 py-3 px-4 rounded-xl text-sm font-medium transition-all duration-200 ${
                mealType === type
                  ? 'bg-white text-[#006036] font-bold shadow-sm'
                  : 'text-stone-500 hover:bg-emerald-50/50'
              }`}
            >
              {type}
            </button>
          ))}
        </div>

        {/* Search bar */}
        <div className="relative group">
          <div className="absolute inset-y-0 left-5 flex items-center pointer-events-none">
            <span className="material-symbols-outlined text-stone-400 group-focus-within:text-[#006036] transition-colors">
              search
            </span>
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search food or scan barcode…"
            className="w-full h-16 pl-14 pr-14 bg-[#e7e8e6] border-none rounded-xl text-base font-medium outline-none focus:ring-4 focus:ring-[#006036]/10 transition-all placeholder:text-stone-400 text-[#191c1b]"
          />
          <button className="absolute inset-y-0 right-4 flex items-center px-2">
            <span className="material-symbols-outlined text-[#006036] p-2 hover:bg-emerald-50 rounded-full transition-colors">
              add_a_photo
            </span>
          </button>
        </div>

        {/* Commonly logged */}
        <div className="space-y-3">
          <h3 className="text-xs uppercase tracking-widest font-bold text-stone-400 px-2">Commonly Logged</h3>
          <div className="grid gap-3">
            {FOODS.filter(f =>
              f.name.toLowerCase().includes(searchQuery.toLowerCase())
            ).map(food => (
              <div
                key={food.name}
                className="flex items-center justify-between p-4 bg-white rounded-xl diffusion-shadow hover:-translate-y-0.5 transition-all border border-[#bec9be]/10"
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-emerald-50 rounded-lg flex items-center justify-center">
                    <span className="material-symbols-outlined text-[#006036]">{food.icon}</span>
                  </div>
                  <div>
                    <p className="font-bold text-[#191c1b] text-sm">{food.name}</p>
                    <p className="text-xs text-stone-400">{food.cal} kcal per {food.unit}</p>
                  </div>
                </div>
                <button
                  onClick={() => handleAdd(food)}
                  className="flex items-center gap-2 px-4 py-2 bg-[#ffddb4] text-[#291800] text-sm font-bold rounded-full hover:shadow-md transition-all"
                >
                  <span className="material-symbols-outlined text-base">add</span>
                  Add
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Right: Current Log & Wellness ───────────────────── */}
      <div className="col-span-12 lg:col-span-5 space-y-6">
        {/* Logged summary */}
        <section className="bg-white p-8 rounded-lg border border-[#bec9be]/10 diffusion-shadow">
          <h2 className="text-xl font-bold font-headline mb-6">Today's {mealType}</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="border-b border-[#edeeeb] text-[#6f7a70] text-[10px] uppercase tracking-widest font-bold">
                <tr>
                  <th className="pb-3">Food</th>
                  <th className="pb-3 text-center">Qty (g)</th>
                  <th className="pb-3 text-right">Cals</th>
                </tr>
              </thead>
              <tbody className="text-sm divide-y divide-[#edeeeb]">
                {loggedItems.map((item, i) => (
                  <tr key={i}>
                    <td className="py-3 font-semibold text-[#191c1b]">{item.name}</td>
                    <td className="py-3 text-center">
                      <input
                        type="number"
                        value={item.qty}
                        onChange={e => handleQtyChange(i, Number(e.target.value))}
                        className="w-16 bg-[#f3f4f1] border-none rounded-md text-center py-1 text-sm outline-none focus:ring-1 focus:ring-[#006036]"
                      />
                    </td>
                    <td className="py-3 text-right font-medium">{item.cal}</td>
                  </tr>
                ))}
                {loggedItems.length === 0 && (
                  <tr>
                    <td colSpan={3} className="py-8 text-center text-stone-400 text-sm">
                      No items logged yet. Add food from the left panel.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Macro pulse */}
          <div className="grid grid-cols-4 gap-2 pt-5 border-t border-[#edeeeb] text-center">
            {[
              { label: 'Calories', val: totalCal, color: 'text-[#006036]' },
              { label: 'Protein', val: '18g', color: 'text-[#191c1b]' },
              { label: 'Carbs', val: '22g', color: 'text-[#191c1b]' },
              { label: 'Fat', val: '11g', color: 'text-[#191c1b]' },
            ].map(m => (
              <div key={m.label}>
                <p className="text-xs text-stone-400 mb-1">{m.label}</p>
                <p className={`text-lg font-bold ${m.color}`}>{m.val}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Wellness section */}
        <section className="bg-[#f3f4f1] p-8 rounded-lg space-y-7">
          {/* Mood */}
          <div>
            <label className="block text-sm font-bold text-stone-600 mb-3">How are you feeling?</label>
            <div className="flex justify-between gap-2">
              {MOODS.map(m => (
                <button
                  key={m}
                  onClick={() => setMood(m)}
                  className={`flex-1 py-4 bg-white rounded-xl text-2xl hover:scale-110 transition-transform shadow-sm ${
                    mood === m ? 'ring-2 ring-[#006036] ring-offset-1' : ''
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          {/* Hunger slider */}
          <div>
            <div className="flex justify-between items-center mb-3">
              <label className="text-sm font-bold text-stone-600">Hunger level</label>
              <span className="text-[#006036] font-bold">{hunger} / 10</span>
            </div>
            <input
              type="range"
              min={1}
              max={10}
              value={hunger}
              onChange={e => setHunger(Number(e.target.value))}
              className="w-full h-2 bg-[#e7e8e6] rounded-full appearance-none cursor-pointer"
            />
            <div className="flex justify-between mt-2 text-[10px] uppercase tracking-tighter text-stone-400 font-bold">
              <span>Full</span>
              <span>Satisfied</span>
              <span>Famished</span>
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-bold text-stone-600 mb-3">Mindful Notes</label>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              rows={3}
              placeholder="Add details about your focus, environment, or taste..."
              className="w-full bg-[#e7e8e6] border-none rounded-xl p-4 text-sm outline-none focus:ring-2 focus:ring-[#006036]/20 placeholder:text-stone-400 resize-none"
            />
          </div>

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={loading || loggedItems.length === 0}
            className="w-full h-14 rounded-full signature-gradient text-white font-bold text-base shadow-lg shadow-[#006036]/20 hover:opacity-90 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? (
              <>
                <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                Saving…
              </>
            ) : (
              <>
                <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
                  check_circle
                </span>
                Save Entry
              </>
            )}
          </button>
        </section>
      </div>
    </div>
  );
}
