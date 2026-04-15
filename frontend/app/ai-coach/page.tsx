'use client';

import { useState, useRef, useEffect } from 'react';
import MessageBubble from '@/components/MessageBubble';
import { Message } from '@/types/chat';

/* ─── Mock conversation history ─────────────────────────────── */
const INITIAL_MESSAGES: Message[] = [
  {
    id: '1',
    role: 'user',
    content: 'What should I eat for dinner tonight? I\'m looking for something healthy but satisfying after a long day.',
    time: '18:42',
  },
  {
    id: '2',
    role: 'ai',
    content: 'Based on your activity levels today and remaining macros, I\'ve curated three premium options that balance complex carbs and lean proteins for optimal recovery. Here are my top picks for you tonight:',
    time: '18:42',
  },
];

const CONVERSATIONS = [
  { id: '1', title: 'What should I eat for dinner?', time: 'Just now', active: true },
  { id: '2', title: 'Protein ideas for post-run',     time: '2 hours ago', active: false },
  { id: '3', title: 'Cheat day advice & balance',     time: 'Yesterday',  active: false },
  { id: '4', title: 'Intermittent fasting schedule',  time: 'Oct 12',     active: false },
];

const FOOD_SUGGESTIONS = [
  { name: 'Zesty Lemon Salmon',   kcal: 420, time: '15 Min', emoji: '🐟' },
  { name: 'Quinoa Harvest Bowl',  kcal: 380, time: '10 Min', emoji: '🥣' },
  { name: 'Ginger Chicken Wok',   kcal: 450, time: '20 Min', emoji: '🥢' },
];

const AI_RESPONSES = [
  'Great question! Based on your logged activity and today\'s macros, I recommend increasing your protein intake slightly. Consider adding a handful of nuts to your next meal.',
  'Your consistency has been excellent this week! For optimal recovery, focus on anti-inflammatory foods like berries, leafy greens, and fatty fish.',
  'I notice you\'ve been logging meals regularly at the same time — that\'s a fantastic habit for your metabolism. Keep it up!',
  'For your fitness goals, aim for a protein-to-carb ratio of 1:2 post-workout. Greek yogurt with banana would be a great option.',
];

let aiIndex = 0;

export default function AiCoachPage() {
  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeChat, setActiveChat] = useState('1');
  const chatRef = useRef<HTMLDivElement>(null);

  /* Auto-scroll to bottom */
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    /* Loading placeholder */
    const loadingMsg: Message = {
      id: (Date.now() + 1).toString(),
      role: 'ai',
      content: '',
      time: '',
      loading: true,
    };

    setMessages(prev => [...prev, userMsg, loadingMsg]);
    setInput('');
    setIsLoading(true);

    /* Simulate API latency — replace with real backend call */
    await new Promise(r => setTimeout(r, 1400));

    const aiMsg: Message = {
      id: (Date.now() + 2).toString(),
      role: 'ai',
      content: AI_RESPONSES[aiIndex % AI_RESPONSES.length],
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    aiIndex++;

    setMessages(prev => prev.filter(m => !m.loading).concat(aiMsg));
    setIsLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  return (
    <div className="flex h-[calc(100vh-80px)] overflow-hidden w-full">
        {/* ── Conversation list ─────────────────────── */}
        <div className="w-72 bg-[#f3f4f1] flex flex-col border-r border-[#bec9be]/10 shrink-0">
          <div className="p-7 pb-4">
            <h2 className="font-headline font-bold text-xl text-[#191c1b]">Conversations</h2>
            <button className="mt-5 w-full py-2.5 px-4 rounded-full border border-[#006036] text-[#006036] font-bold text-sm flex items-center justify-center gap-2 hover:bg-[#9bf6ba]/20 transition-colors">
              <span className="material-symbols-outlined text-base">edit_square</span>
              New Dialogue
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-4 space-y-1 py-2">
            {CONVERSATIONS.map(c => (
              <button
                key={c.id}
                onClick={() => setActiveChat(c.id)}
                className={`w-full text-left p-4 rounded-lg transition-all ${
                  activeChat === c.id
                    ? 'bg-white diffusion-shadow border-l-4 border-[#006036]'
                    : 'hover:bg-[#e7e8e6]/50'
                }`}
              >
                <p className={`text-sm font-medium truncate ${activeChat === c.id ? 'font-bold text-[#191c1b]' : 'text-[#3f4941]'}`}>
                  {c.title}
                </p>
                <p className="text-[10px] text-[#6f7a70] font-medium mt-1">{c.time}</p>
              </button>
            ))}
          </div>
        </div>

        {/* ── Chat area ─────────────────────────────── */}
        <div className="flex-1 flex flex-col bg-white">
          {/* Chat header */}
          <header className="h-16 flex items-center justify-between px-8 bg-surface border-b border-outline-variant/30 hidden">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-full signature-gradient flex items-center justify-center text-white">
                <span className="material-symbols-outlined text-base" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
              </div>
              <div>
                <h3 className="font-headline font-bold text-[#191c1b]">Wellness Coach AI</h3>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#006036] animate-pulse" />
                  <span className="text-[10px] font-bold text-[#006036] uppercase tracking-widest">Active Insight Mode</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button className="p-2 text-[#3f4941] hover:text-[#006036] transition-colors">
                <span className="material-symbols-outlined">search</span>
              </button>
              <button className="p-2 text-[#3f4941] hover:text-[#006036] transition-colors">
                <span className="material-symbols-outlined">more_vert</span>
              </button>
            </div>
          </header>

          {/* Messages */}
          <div ref={chatRef} className="flex-1 overflow-y-auto p-8 space-y-8">
            {messages.map(msg => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {/* Food suggestion cards (only on first message) */}
            {messages.length === 2 && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pl-12">
                {FOOD_SUGGESTIONS.map(food => (
                  <div
                    key={food.name}
                    className="bg-white rounded-lg overflow-hidden diffusion-shadow border border-[#bec9be]/10 group hover:border-[#006036]/20 transition-all cursor-pointer"
                  >
                    <div className="h-28 bg-gradient-to-br from-emerald-50 to-emerald-100 flex items-center justify-center text-5xl group-hover:scale-110 transition-transform duration-300">
                      {food.emoji}
                    </div>
                    <div className="p-4">
                      <h4 className="font-bold text-[#191c1b] text-sm">{food.name}</h4>
                      <div className="flex gap-3 mt-2">
                        <div className="flex items-center gap-1">
                          <span className="material-symbols-outlined text-xs text-[#006036]">local_fire_department</span>
                          <span className="text-[10px] font-bold text-[#6f7a70]">{food.kcal} Kcal</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <span className="material-symbols-outlined text-xs text-[#006036]">schedule</span>
                          <span className="text-[10px] font-bold text-[#6f7a70]">{food.time}</span>
                        </div>
                      </div>
                      <button className="mt-3 w-full py-2 bg-[#feae2c] text-[#291800] rounded-full text-[10px] font-bold uppercase tracking-widest hover:opacity-90 transition-opacity">
                        Add to Meal Plan
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Input area */}
          <footer className="p-8 pt-4 bg-[#f9faf7]/90 backdrop-blur-sm border-t border-stone-100">
            <div className="max-w-4xl mx-auto">
              <div className="relative flex items-center">
                <div className="absolute left-5 flex gap-3 text-[#6f7a70]">
                  <button className="hover:text-[#006036] transition-colors">
                    <span className="material-symbols-outlined">add_circle</span>
                  </button>
                  <button className="hover:text-[#006036] transition-colors">
                    <span className="material-symbols-outlined">mic</span>
                  </button>
                </div>
                <input
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask your coach anything..."
                  disabled={isLoading}
                  className="w-full bg-[#e7e8e6] border-none rounded-full py-5 pl-24 pr-16 text-[#191c1b] placeholder:text-[#6f7a70]/60 outline-none focus:ring-2 focus:ring-[#006036]/20 transition-all diffusion-shadow disabled:opacity-60"
                />
                <button
                  onClick={sendMessage}
                  disabled={isLoading || !input.trim()}
                  className="absolute right-4 w-10 h-10 rounded-full signature-gradient text-white flex items-center justify-center hover:scale-105 transition-transform disabled:opacity-50"
                >
                  {isLoading ? (
                    <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  ) : (
                    <span className="material-symbols-outlined text-base" style={{ fontVariationSettings: "'FILL' 1" }}>send</span>
                  )}
                </button>
              </div>
              <div className="flex justify-center mt-3">
                <div className="flex items-center gap-2 opacity-40">
                  <span className="text-[10px] font-bold uppercase tracking-widest">Powered by Gemini AI</span>
                </div>
              </div>
            </div>
          </footer>
        </div>
    </div>
  );
}
