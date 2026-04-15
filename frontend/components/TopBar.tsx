'use client';

import { useState } from 'react';

interface TopBarProps {
  placeholder?: string;
}

export default function TopBar({ placeholder = 'Search foods or recipes...' }: TopBarProps) {
  const [query, setQuery] = useState('');

  return (
    <header className="flex justify-between items-center w-full h-20 px-8 bg-stone-50/90 backdrop-blur-md sticky top-0 z-40 border-b border-stone-100">
      {/* Search */}
      <div className="flex items-center gap-3 bg-[#e7e8e6] rounded-full px-4 py-2 w-96">
        <span className="material-symbols-outlined text-[#6f7a70] text-xl">search</span>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className="bg-transparent border-none outline-none text-sm w-full placeholder:text-stone-400 text-[#191c1b]"
        />
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-5">
        <button className="text-stone-600 hover:text-emerald-700 transition-colors">
          <span className="material-symbols-outlined">cloud</span>
        </button>
        <button className="text-stone-600 hover:text-emerald-700 transition-colors relative">
          <span className="material-symbols-outlined">notifications</span>
          <span className="absolute top-0 right-0 w-2 h-2 bg-[#835500] rounded-full" />
        </button>
        <div className="w-8 h-px bg-[#bec9be]" />
        <div className="w-9 h-9 rounded-full bg-emerald-200 flex items-center justify-center text-emerald-900 font-bold text-sm">
          AR
        </div>
      </div>
    </header>
  );
}
