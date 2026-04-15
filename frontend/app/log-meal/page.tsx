import type { Metadata } from 'next';
import MealForm from '@/components/MealForm';

export const metadata: Metadata = {
  title: 'Log Meal — clairEat',
  description: 'Fine-tune your nutritional narrative. Log your meals, track macros, and record wellness notes.',
};

export default function LogMealPage() {
  return (
    <>
      <div className="px-8 pb-12 pt-8">
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
      </div>
    </>
  );
}
