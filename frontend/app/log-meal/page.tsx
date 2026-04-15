import type { Metadata } from 'next';
import Sidebar from '@/components/Sidebar';
import TopBar from '@/components/TopBar';
import MealForm from '@/components/MealForm';

export const metadata: Metadata = {
  title: 'Log Meal — clairEat',
  description: 'Fine-tune your nutritional narrative. Log your meals, track macros, and record wellness notes.',
};

export default function LogMealPage() {
  return (
    <div className="min-h-screen bg-[#f9faf7]">
      <Sidebar />
      <div className="ml-64 flex flex-col">
        <TopBar placeholder="Search food or recipes..." />

        <main className="px-8 pb-12 pt-8">
          {/* Header */}
          <header className="flex justify-between items-end mb-10">
            <div>
              <h1 className="text-4xl font-extrabold font-headline tracking-tight text-[#191c1b] mb-2">
                New Entry
              </h1>
              <p className="text-[#6f7a70] font-medium">Fine-tuning your nutritional narrative for today.</p>
            </div>
            <div className="flex items-center gap-4 text-sm font-bold text-[#006036]">
              <span className="px-4 py-2 bg-[#f3f4f1] rounded-full">Thursday, Oct 24</span>
            </div>
          </header>

          <MealForm />
        </main>
      </div>

      {/* AI Coach floating insight */}
      <div className="fixed bottom-8 right-8 max-w-sm glass-panel p-6 rounded-lg diffusion-shadow border border-[#006036]/10 z-40">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full bg-[#006036] flex items-center justify-center animate-pulse">
            <span className="material-symbols-outlined text-white text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
              auto_awesome
            </span>
          </div>
          <span className="text-xs font-bold text-[#006036] tracking-widest uppercase">Coach Insight</span>
        </div>
        <p className="text-sm font-medium text-emerald-900 leading-relaxed">
          Adding blueberries to your yogurt provides a vital antioxidant boost. Your current protein ratio is perfect for muscle recovery today.
        </p>
      </div>
    </div>
  );
}
