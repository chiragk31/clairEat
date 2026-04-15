'use client';

import { useState } from 'react';

interface TopBarProps {
  placeholder?: string;
}

export default function TopBar({ placeholder = 'Search foods or recipes...' }: TopBarProps) {
  const [query, setQuery] = useState('');

  return (
    <header className="flex justify-between items-center w-full h-20 px-8 bg-surface/90 backdrop-blur-md sticky top-0 z-40 border-b border-outline-variant/30">
      {/* Search */}
      <div className="flex items-center gap-3 bg-surface-container-high rounded-full px-4 py-2 w-96">
        <span className="material-symbols-outlined text-outline text-xl">search</span>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className="bg-transparent border-none outline-none text-sm w-full placeholder:text-on-surface-variant text-on-surface"
        />
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-5">
        <button className="text-on-surface-variant hover:text-primary transition-colors">
          <span className="material-symbols-outlined">cloud</span>
        </button>
        <button className="text-on-surface-variant hover:text-primary transition-colors relative">
          <span className="material-symbols-outlined">notifications</span>
          <span className="absolute top-0 right-0 w-2 h-2 bg-error rounded-full" />
        </button>
        <div className="w-8 h-px bg-outline-variant" />
        <div className="w-9 h-9 rounded-full bg-primary-container/20 flex items-center justify-center text-primary font-bold text-sm">
          AR
        </div>
      </div>
    </header>
  );
}
