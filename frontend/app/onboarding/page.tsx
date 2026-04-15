'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
const STEPS = ['Welcome', 'Personal Blueprint', 'Goals & Diet', 'Ready to Go'];

const GOAL_OPTIONS = ['Weight Loss', 'Muscle Gain', 'Maintenance', 'Diabetes Control'];
const DIET_OPTIONS = ['Vegetarian', 'Vegan', 'Gluten-Free', 'Lactose-Free'];
const ACTIVITY_LEVELS = [
  'Sedentary (Office job, little exercise)',
  'Lightly Active (1-2 days/week)',
  'Moderately Active (3-5 days/week)',
  'Very Active (6-7 days/week)',
  'Extra Active (Physical labor or pro training)',
];

interface FormData {
  name: string;
  gender: string;
  age: string;
  height: string;
  weight: string;
  activity: string;
  goals: string[];
  diets: string[];
  allergies: string;
}

export default function OnboardingPage() {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState<FormData>({
    name: '', gender: '', age: '', height: '', weight: '',
    activity: ACTIVITY_LEVELS[2],
    goals: ['Muscle Gain'], diets: ['Gluten-Free'], allergies: '',
  });

  const pct = Math.round(((step - 1) / (STEPS.length - 1)) * 100);

  const toggleTag = (field: 'goals' | 'diets', val: string) => {
    setForm(prev => ({
      ...prev,
      [field]: prev[field].includes(val)
        ? prev[field].filter(v => v !== val)
        : [...prev[field], val],
    }));
  };

  return (
    <main className="flex min-h-screen flex-col md:flex-row">
      {/* ── Left hero ───────────────────────────────── */}
      <section className="relative w-full md:w-1/2 min-h-[360px] md:min-h-screen flex items-center justify-center overflow-hidden">
        {/* Gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#006036] via-[#1a7a4a] to-emerald-900" />
        {/* Decorative blobs */}
        <div className="absolute top-20 left-16 w-64 h-64 bg-[#9bf6ba]/10 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-80 h-80 bg-[#feae2c]/10 rounded-full blur-3xl" />

        <div className="relative z-10 p-12 text-center md:text-left w-full max-w-xl">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-10">
            <div className="bg-white p-3 rounded-xl diffusion-shadow">
              <span className="material-symbols-outlined text-[#006036] text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                restaurant
              </span>
            </div>
            <span className="font-headline font-extrabold text-3xl text-white tracking-tight">clairEat</span>
          </div>

          <h1 className="font-headline font-bold text-5xl md:text-6xl text-white mb-6 leading-tight">
            Your AI-Powered <br />
            <span className="text-[#9bf6ba]">Nutrition Coach</span>
          </h1>
          <p className="text-white/70 text-lg max-w-md">
            Personalized meal plans and intelligent insights to help you reach your wellness goals effortlessly.
          </p>

          {/* Feature bullets */}
          <div className="mt-10 space-y-3">
            {[
              { icon: 'psychology',  text: 'AI-powered meal recommendations' },
              { icon: 'trending_up', text: 'Real-time nutritional tracking' },
              { icon: 'emoji_events',text: 'Goal-based habit coaching' },
            ].map(f => (
              <div key={f.text} className="flex items-center gap-3 text-white/80">
                <span className="material-symbols-outlined text-[#9bf6ba] text-lg" style={{ fontVariationSettings: "'FILL' 1" }}>
                  {f.icon}
                </span>
                <span className="text-sm font-medium">{f.text}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Right onboarding form ────────────────────── */}
      <section className="w-full md:w-1/2 bg-[#f9faf7] flex flex-col px-6 md:px-16 py-12 overflow-y-auto">
        <div className="w-full max-w-xl mx-auto">
          {/* Progress */}
          <div className="mb-10">
            <div className="flex justify-between items-end mb-4">
              <div>
                <span className="text-xs font-medium text-[#6f7a70]">Step {step} of {STEPS.length}</span>
                <h2 className="font-headline font-semibold text-2xl text-[#191c1b] mt-0.5">{STEPS[step - 1]}</h2>
              </div>
              <span className="text-sm font-bold text-[#006036]">{pct}% Complete</span>
            </div>
            <div className="h-1.5 w-full bg-[#e7e8e6] rounded-full overflow-hidden">
              <div
                className="h-full signature-gradient rounded-full transition-all duration-500"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>

          {/* Step 1: Welcome */}
          {step === 1 && (
            <div className="space-y-6 text-center">
              <div className="w-24 h-24 signature-gradient rounded-3xl flex items-center justify-center mx-auto diffusion-shadow">
                <span className="material-symbols-outlined text-white text-5xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                  waving_hand
                </span>
              </div>
              <h3 className="text-3xl font-bold font-headline text-[#191c1b]">Welcome to clairEat</h3>
              <p className="text-[#3f4941] max-w-sm mx-auto">
                Let&apos;s set up your personal nutrition profile in just a few steps. It takes under 2 minutes.
              </p>
              <div className="grid grid-cols-3 gap-4 mt-8">
                {[
                  { icon: 'restaurant', label: 'AI Meal Plans' },
                  { icon: 'bar_chart', label: 'Progress Tracking' },
                  { icon: 'psychology', label: 'Smart Coaching' },
                ].map(f => (
                  <div key={f.label} className="bg-white rounded-xl p-5 text-center diffusion-shadow">
                    <span className="material-symbols-outlined text-[#006036] text-2xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                      {f.icon}
                    </span>
                    <p className="text-xs font-bold text-[#3f4941] mt-2">{f.label}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Step 2: Personal Blueprint */}
          {step === 2 && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-semibold text-on-surface-variant mb-2">Full Name</label>
                  <Input
                    type="text"
                    value={form.name}
                    onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
                    placeholder="e.g. Alex Rivera"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-on-surface-variant mb-2">Gender</label>
                  <select
                    value={form.gender}
                    onChange={e => setForm(p => ({ ...p, gender: e.target.value }))}
                    className="w-full h-14 bg-surface-container border-none rounded-xl px-4 outline-none focus:ring-2 focus:ring-primary/20 text-on-surface"
                  >
                    <option value="">Select Gender</option>
                    <option>Female</option><option>Male</option>
                    <option>Non-binary</option><option>Prefer not to say</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                {[
                  { label: 'Age', key: 'age', placeholder: 'Years', type: 'number' },
                  { label: 'Height', key: 'height', placeholder: 'cm', type: 'text' },
                  { label: 'Weight', key: 'weight', placeholder: 'kg', type: 'text' },
                ].map(f => (
                  <div key={f.key}>
                    <label className="block text-sm font-semibold text-on-surface-variant mb-2">{f.label}</label>
                    <Input
                      type={f.type}
                      value={form[f.key as keyof FormData] as string}
                      onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))}
                      placeholder={f.placeholder}
                    />
                  </div>
                ))}
              </div>

              <div>
                <label className="block text-sm font-semibold text-[#3f4941] mb-2">Daily Activity Level</label>
                <select
                  value={form.activity}
                  onChange={e => setForm(p => ({ ...p, activity: e.target.value }))}
                  className="w-full h-14 bg-[#e7e8e6] border-none rounded-md px-4 outline-none focus:ring-2 focus:ring-[#006036]/20 text-[#191c1b]"
                >
                  {ACTIVITY_LEVELS.map(a => <option key={a}>{a}</option>)}
                </select>
              </div>
            </div>
          )}

          {/* Step 3: Goals & Diet */}
          {step === 3 && (
            <div className="space-y-8">
              <div>
                <label className="block text-sm font-semibold text-[#3f4941] mb-3">Health Goals</label>
                <div className="flex flex-wrap gap-3">
                  {GOAL_OPTIONS.map(g => (
                    <button
                      key={g}
                      onClick={() => toggleTag('goals', g)}
                      className={`px-5 py-2.5 rounded-full text-sm font-medium border transition-all ${
                        form.goals.includes(g)
                          ? 'bg-[#abffc6] text-[#006036] border-[#006036]/30 font-semibold'
                          : 'border-[#bec9be] text-[#191c1b] hover:bg-[#edeeeb]'
                      }`}
                    >
                      {g}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-[#3f4941] mb-3">Dietary Preferences</label>
                <div className="flex flex-wrap gap-3">
                  {DIET_OPTIONS.map(d => (
                    <button
                      key={d}
                      onClick={() => toggleTag('diets', d)}
                      className={`px-5 py-2.5 rounded-full text-sm font-medium border transition-all ${
                        form.diets.includes(d)
                          ? 'bg-[#abffc6] text-[#006036] border-[#006036]/30 font-semibold'
                          : 'border-[#bec9be] text-[#191c1b] hover:bg-[#edeeeb]'
                      }`}
                    >
                      {d}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-on-surface-variant mb-2">Specific Allergies</label>
                <Input
                  icon="search"
                  type="text"
                  value={form.allergies}
                  onChange={e => setForm(p => ({ ...p, allergies: e.target.value }))}
                  placeholder="Add ingredients to avoid..."
                />
              </div>
            </div>
          )}

          {/* Step 4: Ready */}
          {step === 4 && (
            <div className="text-center space-y-6">
              <div className="w-24 h-24 signature-gradient rounded-3xl flex items-center justify-center mx-auto diffusion-shadow">
                <span className="material-symbols-outlined text-white text-5xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                  check_circle
                </span>
              </div>
              <h3 className="text-3xl font-bold font-headline text-[#191c1b]">You&apos;re all set, {form.name || 'Champion'}!</h3>
              <p className="text-[#3f4941] max-w-sm mx-auto">
                Your personalized nutrition profile is ready. Let's start your wellness journey.
              </p>
              <div className="bg-white rounded-xl p-6 text-left diffusion-shadow space-y-3">
                <p className="text-xs font-bold text-[#6f7a70] uppercase">Your Profile Summary</p>
                {form.goals.length > 0 && (
                  <p className="text-sm text-[#191c1b]">
                    <span className="font-bold">Goals:</span> {form.goals.join(', ')}
                  </p>
                )}
                {form.diets.length > 0 && (
                  <p className="text-sm text-[#191c1b]">
                    <span className="font-bold">Diet:</span> {form.diets.join(', ')}
                  </p>
                )}
                <p className="text-sm text-[#191c1b]">
                  <span className="font-bold">Activity:</span> {form.activity.split('(')[0].trim()}
                </p>
              </div>
            </div>
          )}

          {/* Navigation buttons */}
          <div className="pt-10 flex items-center justify-between">
            {step > 1 ? (
              <Button
                variant="ghost"
                onClick={() => setStep(s => s - 1)}
                className="gap-2 text-primary"
              >
                <span className="material-symbols-outlined">arrow_back</span>
                Back
              </Button>
            ) : (
              <div />
            )}

            {step < STEPS.length ? (
              <Button
                variant="primary"
                onClick={() => setStep(s => s + 1)}
                className="gap-2 px-10 h-12 text-white signature-gradient"
              >
                Continue
                <span className="material-symbols-outlined">arrow_forward</span>
              </Button>
            ) : (
              <Link
                href="/"
                className="inline-flex items-center justify-center font-bold font-sans rounded-full transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none bg-primary text-on-primary hover:bg-primary/90 shadow-md gap-2 px-10 h-12 text-white signature-gradient"
              >
                Go to Dashboard
                <span className="material-symbols-outlined">arrow_forward</span>
              </Link>
            )}
          </div>

          <p className="text-xs text-[#6f7a70] text-center mt-8">
            Your privacy is important. We use this data strictly to calibrate your nutritional targets.
          </p>
        </div>
      </section>
    </main>
  );
}
